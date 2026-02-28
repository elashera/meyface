**Purpose**
`yt-dlp` is a command-line media downloader. This workspace now also includes a minimal local desktop UI (`audio_ui.py`) to download audio from YouTube/YouTube Music without typing commands.

**Architecture**
- CLI core remains unchanged: `yt_dlp/__main__.py` -> `yt_dlp.main()` -> option parsing -> extractor selection -> downloader -> postprocessors.
- New UI layer: `audio_ui.py` (Tkinter) is a thin wrapper that launches the local CLI via `python -m yt_dlp`.
- UI process model: a background thread runs `subprocess.Popen(...)`; stdout/stderr lines are streamed into a queue and rendered in a log text area.

**Directory Structure**
- `yt_dlp/`: core library and CLI logic.
- `yt_dlp/extractor/`: site-specific extractors.
- `yt_dlp/downloader/`: protocol/file download implementations.
- `yt_dlp/postprocessor/`: ffmpeg-based and metadata post-processing.
- `audio_ui.py`: simple desktop UI for audio-only downloads.

**Core Models**
- `YoutubeDL` (`yt_dlp/YoutubeDL.py`): orchestrates extraction, format selection, download, and postprocessing.
- `AudioDownloaderUI` (`audio_ui.py`): GUI state container for URL, output format, output directory, current subprocess, and log queue.

**Key Features**
- URL input box for YouTube/YouTube Music links.
- Output mode selector:
- `MP3 320 kbps`: `-f ba[acodec*=opus]/ba -x --audio-format mp3 --audio-quality 320K`
- `AAC`: `-f ba[acodec*=opus]/ba -x --audio-format aac --audio-quality 0`
- `Opus (sin conversion)`: `-f ba[acodec*=opus]/ba`
- Output folder picker and custom output template `%(title)s [%(id)s].%(ext)s`.
- Live log window, start/stop controls, and completion status.

**Manual Xcode Steps**
None. This project is Python-based; no Xcode configuration is required.

**Next Technical Steps**
- Add URL validation and clearer user-facing error mapping for common yt-dlp/ffmpeg failures.
- Add a packaged entry point (e.g., console script) to run the UI directly.
- Optionally add persisted UI settings (last folder and last format).
