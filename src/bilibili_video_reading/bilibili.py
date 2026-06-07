from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit

from .common import normalize_bvid_or_value
from .net import fetch, fetch_json


MIXIN_KEY_ENC_TAB = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]


def resolve_video(source: str, *, proxy: str | None = None) -> dict:
    bvid = normalize_bvid_or_value(source)
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={quote(str(bvid))}"
    data = fetch_json(url, proxy=proxy)
    if data.get("code") != 0:
        raise RuntimeError(f"view API failed: {data}")
    info = data["data"]
    pages = info.get("pages") or []
    if not pages:
        raise RuntimeError("No pages/cid found in view API response")
    return {
        "aid": info["aid"],
        "bvid": info["bvid"],
        "cid": pages[0]["cid"],
        "title": info.get("title") or info["bvid"],
        "pages": pages,
    }


def normalize_subtitle_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("//"):
        return "https:" + url
    return url


def subtitles_from_player_data(data: dict) -> list[dict]:
    subs = ((data.get("data") or {}).get("subtitle") or {}).get("subtitles") or []
    result = []
    for sub in subs:
        sub_url = normalize_subtitle_url(sub.get("subtitle_url"))
        if sub_url:
            result.append(
                {
                    "code": sub.get("lan") or sub.get("lan_doc") or "unknown",
                    "label": sub.get("lan_doc") or sub.get("lan") or "unknown",
                    "url": sub_url,
                }
            )
    return result


def public_player_subtitles(bvid: str, cid: int, *, proxy: str | None = None) -> tuple[list[dict], dict]:
    url = f"https://api.bilibili.com/x/player/v2?bvid={quote(bvid)}&cid={cid}"
    data = fetch_json(url, proxy=proxy)
    return subtitles_from_player_data(data), data


def extract_wbi_key(wbi_url: str | None) -> str | None:
    if not wbi_url:
        return None
    return Path(urlsplit(wbi_url).path).stem


def get_mixin_key(img_key: str, sub_key: str) -> str:
    raw = img_key + sub_key
    return "".join(raw[index] for index in MIXIN_KEY_ENC_TAB)[:32]


def get_wbi_keys(*, proxy: str | None = None) -> tuple[str, str]:
    data = fetch_json("https://api.bilibili.com/x/web-interface/nav", proxy=proxy)
    wbi_img = ((data.get("data") or {}).get("wbi_img") or {})
    img_key = extract_wbi_key(wbi_img.get("img_url"))
    sub_key = extract_wbi_key(wbi_img.get("sub_url"))
    if not img_key or not sub_key:
        raise RuntimeError(f"Could not find WBI keys in nav response: {data}")
    return img_key, sub_key


def signed_wbi_params(params: dict, *, proxy: str | None = None) -> dict:
    img_key, sub_key = get_wbi_keys(proxy=proxy)
    mixin_key = get_mixin_key(img_key, sub_key)
    signed = {key: re.sub(r"[!'()*]", "", str(value)) for key, value in params.items() if value is not None}
    signed["wts"] = str(int(time.time()))
    sorted_items = sorted(signed.items())
    query = urlencode(sorted_items, quote_via=quote)
    signed["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return signed


def wbi_player_subtitles(
    bvid: str,
    aid: int | None,
    cid: int,
    *,
    proxy: str | None = None,
) -> tuple[list[dict], dict]:
    params = signed_wbi_params({"bvid": bvid, "aid": aid, "cid": cid}, proxy=proxy)
    url = "https://api.bilibili.com/x/player/wbi/v2?" + urlencode(params, quote_via=quote)
    data = fetch_json(url, proxy=proxy)
    return subtitles_from_player_data(data), data


def subtitle_index_url(aid: int, cid: int) -> str:
    params = {
        "oid": str(cid),
        "pid": str(aid),
        "context_ext": json.dumps({"video_type": 1}, separators=(",", ":")),
        "type": "1",
        "cur_production_type": "0",
    }
    return "https://api.bilibili.com/x/v2/subtitle/web/view?" + urlencode(params, quote_via=quote)


def parse_binary_subtitle_index(data: bytes) -> list[dict]:
    url_pattern = re.compile(
        rb"//(?:subtitle\.bilibili\.com|aisubtitle\.hdslb\.com)/[^\x00-\x20\"'<>]+?"
        rb"auth_key=\d+-[0-9a-fA-F]+-0-[0-9a-fA-F]+",
        re.S,
    )
    lang_pattern = re.compile(rb"ai-[a-z]+|zh(?:-[A-Z]+)?|en(?:-[A-Z]+)?")
    items = []
    seen = set()
    for match in url_pattern.finditer(data):
        prefix = data[max(0, match.start() - 160) : match.start()]
        lang_matches = list(lang_pattern.finditer(prefix))
        code = lang_matches[-1].group(0).decode("ascii", errors="ignore") if lang_matches else "unknown"
        url = "https:" + match.group(0).decode("ascii", errors="ignore")
        key = (code, url)
        if key not in seen:
            seen.add(key)
            items.append({"code": code, "label": code, "url": url})
    return items


def subtitle_url_rank(url: str | None) -> int:
    if "aisubtitle.hdslb.com" in (url or ""):
        return 0
    if "subtitle.bilibili.com" in (url or ""):
        return 1
    return 2


def choose_subtitle(items: list[dict], lang: str) -> dict | None:
    if not items:
        return None
    preferred = [lang, f"ai-{lang}", "zh", "ai-zh"] if lang == "zh" else [lang, f"ai-{lang}"]
    for code in preferred:
        matches = [item for item in items if item.get("code") == code]
        if matches:
            return sorted(matches, key=lambda item: subtitle_url_rank(item.get("url")))[0]
    for item in items:
        code = item.get("code") or ""
        if lang in code:
            return item
    return sorted(items, key=lambda item: subtitle_url_rank(item.get("url")))[0]


def page_label(page_info: dict | None) -> str | None:
    page_number = page_info.get("page") if page_info else None
    part = page_info.get("part") if page_info else None
    if page_number and part:
        return f"P{page_number}: {part}"
    if page_number:
        return f"P{page_number}"
    return None


def page_stem(stem_base: str, page_info: dict | None, *, include_page: bool) -> str:
    if not include_page or not page_info:
        return stem_base
    page_number = int(page_info.get("page") or 1)
    return f"{stem_base}_p{page_number:02d}"
