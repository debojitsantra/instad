<p align="center">
  <img src="images/full_logo.png" width="400" style="border-radius: 24px;" alt="Backlog Tracker Logo" referrerPolicy="no-referrer" />
</p>


#### **Instad** is a Python-based yt-dlp GUI for fetching videos, playlists, clips, posts, reels, and audio from platforms supported by `yt-dlp`.

## Legal Copyright Disclaimer

> [!CAUTION]
> Please be aware that videos on platforms like YouTube may be protected by copyright (DMCA). The creator of Instad does not support, and cannot be held accountable for, any use of this application that infringes upon these legal protections.

---

## Features
- Download any URL supported by yt-dlp
- add multiple urls in queue
- Download playlists when present
- Choose between quality
- Paste cookies in Settings for age-restricted, private, or signed-in downloads
- Accepts Netscape `cookies.txt` exports or a raw browser `Cookie:` header
- Modern  GUI built with `customtkinter`
- Automatic fallback to TUI mode if no graphical display is available

---

## Requirements
- Python 3.13+
- ffmpeg installed and available in PATH
- Deno installed and available in PATH (for YouTube signature solving)
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
# Debian
sudo apt install ffmpeg -y
# Arch
sudo sudo pacman -S ffmpeg
# Fedora
sudo dnf install ffmpeg
```
### Install Deno

**Windows**
```powershell
irm https://deno.land/install.ps1 | iex
```
**Linux/WSL**
```bash
curl -fsSL https://deno.land/install.sh | sh
```
##### Linux Requirements

If the app fails to start with a Fontconfig or font-related error, install:

```bash
## Debian
sudo apt install -y fontconfig fonts-dejavu-core fonts-liberation2
## Arch
sudo pacman -S fontconfig ttf-dejavu ttf-liberation
## Fedora
sudo dnf install fontconfig dejavu-sans-fonts liberation-fonts
```

(Required for some Linux distributions and WSL setups.)

---

## Screenshots

<p align="center">
  <img src="images/1.png" width="60%" alt="Screenshot 1" />
  <img src="images/2.png" width="60%" alt="Screenshot 2" />
  <img src="images/3.png" width="60%" alt="Screenshot 3" />
  <img src="images/4.png" width="60%" alt="Screenshot 4" />
  <img src="images/5.png" width="60%" alt="Screenshot 5" />
</p>

## Usage

```bash
python instad.py
```


---

## Cookies

Use Settings -> Cookies for videos that require a signed-in account, such as age-restricted or private content.

Paste either:
- A Netscape `cookies.txt` export.
- A raw browser `Cookie:` header copied from a signed-in request.

Refresh the pasted cookies if a download fails with an authentication or age-restriction error.

---

## Pre-built Binaries

Download the latest release for your platform from the [Releases](../../releases) page:


---

## Building from Source

```bash
pip install pyinstaller

# Windows
pyinstaller --noconfirm --onefile --noconsole --icon "assets/icon.ico" --add-data "assets;assets" --name instad instad.py

# Linux
pyinstaller --onefile --add-data "assets:assets" instad.py
```

Output binary will be in `dist/`. For a custom Windows executable icon, convert `assets/icon.svg` to `.ico` and pass it with `--icon path\to\icon.ico`.

---

## Releases (CI/CD)

Releases are built automatically via GitHub Actions on every version tag push:

```bash
git tag v1.2.0.1
git push origin v1.2.0.1
```

This triggers automated Windows (.exe) and Linux binary builds, published to GitHub Releases.

---

## Supported Platforms

| Site | Type |
|---|---|
| Any yt-dlp supported site | Video / Audio / Playlists / Metadata supported by that extractor |

---

## License
See [LICENSE](LICENSE)

##  You can help me by Donating
[![Ko-Fi](https://img.shields.io/badge/Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/debojitsantra) 
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/debojitsantra/donate)
<a href="https://chai4.me/debojitsantra" target="_blank" title="Support debojitsantra on Chai4Me" style="display:inline-flex;flex-direction:column;align-items:center;justify-content:center;background:#ffffff;padding:8px 32px;border-radius:16px;text-decoration:none;border:1px solid #e5e7eb;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);transition:transform 0.2s;"><img src="https://chai4.me/icons/wordmark.png" alt="Chai4Me" style="height:32px;object-fit:contain;"/></a>
