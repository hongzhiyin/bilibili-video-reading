# Manual DevTools Fallback

Use this only when the AI can verify subtitles are visible in Chrome but cannot retrieve the final JSON through shell or browser APIs.

1. Open Chrome DevTools.
2. Select Network.
3. Enable Preserve log.
4. Clear current requests.
5. Toggle subtitles off, then select the desired language again.
6. Filter for `aisubtitle`, `subtitle`, or `auth_key`.
7. Prefer the `aisubtitle.hdslb.com` request; otherwise select the subtitle JSON request.
8. Copy only the Response body.
9. Save it as `<stem>_<lang>.json`.
10. Run:

```bash
bvr subtitles convert <stem>_<lang>.json --output-dir .
```

Do not copy request headers, cookies, or `Copy as cURL`.
