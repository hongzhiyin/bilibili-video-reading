# ASR/OCR Fallback

Use this only after public subtitles, WBI subtitles, subtitle index parsing, logged-in Chrome triggering, and Response-only fallback fail or confirm that the video has no usable subtitle track.

## Decision

- Speech-heavy videos: extract/download audio and transcribe with ASR.
- Screen recordings, slides, code demos, gameplay, or hard subtitles: combine ASR with sampled frames and OCR/vision.
- Purely visual videos: sample frames/keyframes and use a vision model; mention that there is no reliable speech transcript.
- Music/MMD/character-showcase clips: ASR may only capture unreliable lyrics. Use sampled frames and visual notes as the primary evidence.

Before choosing a branch, check local tool availability:

```bash
bvr tools doctor
```

## Safe Login Handling

Do not read browser cookies or profile files for `yt-dlp`, `BBDown`, or any downloader. If public media download fails because login is required, ask the user for one of these safer inputs:

- A local video/audio file they already downloaded.
- Permission to use the visible logged-in browser only to trigger page resources, without extracting credentials.
- Manual subtitle JSON `Response` body if subtitles exist.

## Audio ASR Path

When public download is allowed, first try audio-only download:

```bash
bvr media download \
  "https://www.bilibili.com/video/BV..." \
  --audio-only \
  --output-dir ./bilibili-video-reading-tmp/BV...
```

If `yt-dlp` returns HTTP 412, retry once with the CLI defaults, which include a Chrome-like User-Agent and `https://www.bilibili.com/` referer. Do not use `--cookies`, `--cookies-from-browser`, or browser profile files.

Then transcribe with the best available local or API ASR tool. Preserve timestamps if available, and save:

- `<stem>_asr.srt`
- `<stem>_asr_transcript.txt`

If using an external transcription API, confirm with the user before uploading private or login-gated media.

When `ffmpeg`, `whisper-cli`, and a GGML model are available, prefer:

```bash
bvr asr whisper-cpp \
  <audio-file> \
  --lang zh \
  --output-dir ./bilibili-video-reading-tmp/BV... \
  --stem <stem>_asr
```

The CLI detects GGML models from explicit `--model`, `WHISPER_CPP_MODEL`, `BVR_WHISPER_MODEL`, `BVR_ASSET_DIR`, local external `models/whisper/...`, or installed skill assets. It defaults to CPU mode (`whisper-cli -ng`) because Metal/GPU may fail with buffer allocation errors in Codex. Use `--gpu` only after CPU mode is known to work.

Useful local ASR installs to ask the user for when missing:

- `brew install ffmpeg`: enables audio conversion and reliable frame sampling.
- `brew install yt-dlp`: enables public media download.
- `brew install whisper-cpp` or `pip install mlx-whisper`: local transcription without uploading media.
- `pip install faster-whisper`: local transcription with good timestamp support, but it may require model downloads and more disk space.

## Frame/OCR Path

For Bilibili URLs or local video files, prefer:

```bash
bvr media sample \
  "https://www.bilibili.com/video/BV..." \
  --output-dir ./bilibili-video-reading-tmp/BV...
```

The CLI safely downloads public media with `yt-dlp` using a Chrome-like User-Agent and Referer, or accepts a local video file path. It creates:

- `frames/frame_*.jpg`
- `frames_index.csv`
- `contact_sheet.jpg`
- `<stem>_visual_notes.md`
- `manifest.json`

It samples short videos densely, longer videos sparsely, and caps the initial frame count to avoid flooding the workspace. Override with `--sample-every <seconds>` or `--max-frames <count>` only when the first pass misses important fast action, code changes, slide transitions, or hard subtitles.

For local files:

```bash
bvr media sample \
  <video-file> \
  --output-dir ./bilibili-video-reading-tmp/<stem>
```

After sampling, inspect `contact_sheet.jpg` first, then open individual frames as needed. Run OCR or a vision model on sampled frames, then merge the visual notes with the ASR transcript by timestamp.

Manual ffmpeg fallback:

```bash
ffmpeg -i <video-file> -vf fps=1/10 <stem>_frames/frame_%05d.jpg
```

If `ffmpeg` is unavailable but Chrome can play the video, use Chrome progress-bar seeking and screenshots as a fallback. Keep notes with approximate timestamps and say this is visual/OCR-derived, not a full transcript.

## Final Answer

When answering the user, say which source was used:

- official/AI subtitle
- logged-in Chrome-triggered subtitle URL
- ASR transcript
- OCR/vision frame notes

If the result is ASR/OCR-derived, mention that it may miss visual or audio details that were not captured by sampling/transcription.
