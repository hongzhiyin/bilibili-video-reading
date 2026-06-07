from __future__ import annotations

import ipaddress
import json
import socket
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener, urlopen

from .common import DEFAULT_REFERER, DEFAULT_USER_AGENT


SENSITIVE_QUERY_KEYS = {
    "auth_key",
    "bili_ticket",
    "buvid3",
    "csrf",
    "csrf_token",
    "key",
    "sessdata",
    "sid",
    "token",
    "w_rid",
}
FAKE_IP_NETWORKS = [ipaddress.ip_network("198.18.0.0/15")]


def fetch(
    url: str,
    *,
    binary: bool = False,
    referer: str = DEFAULT_REFERER,
    proxy: str | None = None,
) -> bytes | str:
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Referer": referer,
        "Accept": "*/*",
    }
    req = Request(url, headers=headers)
    if proxy:
        opener = build_opener(ProxyHandler({"http": proxy, "https": proxy}))
        response_context = opener.open(req, timeout=20)
    else:
        response_context = urlopen(req, timeout=20)
    with response_context as response:
        data = response.read()
    return data if binary else data.decode("utf-8", errors="replace")


def fetch_json(url: str, *, referer: str = DEFAULT_REFERER, proxy: str | None = None) -> dict:
    return json.loads(fetch(url, referer=referer, proxy=proxy))


def redact_url(url: str) -> str:
    if not isinstance(url, str) or "?" not in url:
        return url
    parts = urlsplit(url)
    redacted_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in SENSITIVE_QUERY_KEYS or "token" in lowered or "auth" in lowered:
            redacted_query.append((key, "REDACTED"))
        else:
            redacted_query.append((key, value))
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(redacted_query, quote_via=quote),
            parts.fragment,
        )
    )


def redact_for_output(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if isinstance(item, str) and "url" in lowered:
                result[key] = redact_url(item)
            elif lowered in SENSITIVE_QUERY_KEYS:
                result[key] = "<redacted>"
            else:
                result[key] = redact_for_output(item)
        return result
    if isinstance(value, list):
        return [redact_for_output(item) for item in value]
    if isinstance(value, str):
        return redact_url(value)
    return value


def is_fake_ip_address(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(ip in network for network in FAKE_IP_NETWORKS)


def resolve_host_for_diagnostics(host: str) -> dict:
    result = {"host": host, "addresses": [], "fake_ip": False}
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except Exception as exc:
        result["error"] = str(exc)
        return result
    addresses = sorted({info[4][0] for info in infos if info and info[4]})
    result["addresses"] = addresses
    result["fake_ip"] = any(is_fake_ip_address(address) for address in addresses)
    return result


def subtitle_endpoint_diagnostics(url: str) -> dict:
    host = urlsplit(url).hostname or ""
    result = {"host": host}
    if host:
        result["host_resolution"] = resolve_host_for_diagnostics(host)
    if host == "subtitle.bilibili.com":
        result["host_note"] = (
            "subtitle.bilibili.com short URLs are often less stable than final "
            "aisubtitle.hdslb.com JSON URLs; prefer a Chrome-triggered final URL "
            "when direct download fails."
        )
    return result
