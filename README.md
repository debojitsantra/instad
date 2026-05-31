# Instad: Universal Media Downloader

Instad is a Python-based media downloader for fetching photos, videos, and audio from multiple platforms including Instagram, YouTube, Soundgasm, Reddit, and Facebook & Platforms supported by Yt-dlp.  
It uses `instaloader` and `yt-dlp` under the hood to deliver reliable, high-quality downloads.

---

## Features
- Download public Instagram posts and profiles
- YouTube downloads with quality selection (Audio Only MP3, 360p, 480p, 720p, 1080p, Best)
- Soundgasm downloads automatically converted to MP3
- Facebook and Reddit media downloads at best available quality
- Detects private Instagram profiles and handles them safely
- Modern dark GUI built with `customtkinter`
- Automatic fallback to TUI mode if no graphical display is available
- Cross-platform: Windows and Linux supported

---

## Requirements
- Python 3.11+
- ffmpeg installed and available in PATH
- Dependencies listed in `requirements.txt`

---

## Installation

```bash
git clone https://github.com/debojitsantra/instad.git
cd instad
python -m venv venv
# Windows
venv\Scripts\activate
# Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Install ffmpeg
**Windows:**
```powershell
winget install Gyan.FFmpeg
```
**Linux/WSL:**
```bash
sudo apt install ffmpeg -y
```

---

## Usage

```bash
python instad.py
```

Launches GUI on supported systems. Falls back to TUI automatically on headless/Linux environments without a display.

---

## Pre-built Binaries

Download the latest release for your platform from the [Releases](../../releases) page:

| Platform | File |
|---|---|
| Windows | `instad.exe` |
| Linux | `instad` |

---

## Building from Source

```bash
pip install pyinstaller

# Windows
pyinstaller --onefile --console instad.py

# Linux
pyinstaller --onefile instad.py
```

Output binary will be in `dist/`.

---

## Releases (CI/CD)

Releases are built automatically via GitHub Actions on every version tag push:

```bash
git tag v1.0.1
git push origin v1.0.1
```

This triggers automated Windows (.exe) and Linux binary builds, published to GitHub Releases.

---

## Supported Platforms

| Site | Type |
|---|---|
| YouTube | Video / Audio |
| Instagram | Posts / Profiles |
| Soundgasm | Audio (Converted to MP3) |
| Facebook | Video |
| Reddit | Video |
| Other Generic Platforms Supported by Yt-dlp| Video/Audio|

---

## License
See [LICENSE](LICENSE)

##  You can help me by Donating
[![Ko-Fi](https://img.shields.io/badge/Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/debojitsantra) 
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/debojitsantra/donate)
