# Instad: Universal Media Downloader

Instad is a Python-based media downloader that allows you to easily fetch photos, videos, and audio from multiple platforms including Instagram, YouTube, Soundgasm, Reddit, and Facebook.  
It uses `instaloader` and `yt-dlp` under the hood to deliver reliable, high-quality downloads.

---

## Features
- Download public Instagram posts and profiles  
- YouTube downloads with quality selection (Audio, 360p,1080p, Best)  
- Soundgasm downloads automatically converted to MP3  
- Facebook and Reddit media downloads at best available quality  
- Detects private Instagram profiles and handles them safely  
- Modern GUI built with `customtkinter`  
- Automatic fallback to terminal mode if no graphical display is detected  
- Optional Instagram session loading for private or rate-limited profiles  
- Change download directory directly from the GUI  
- Progress bar support for both GUI and terminal modes

---

## Prerequisites
- Python 3.8 or later  
- `ffmpeg` (for media conversion)  
- Required Python libraries listed in `requirements.txt`

---



## Installation

1. Clone the repository or download the latest release.  
2. Navigate into the project folder.  
3. Install all dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### GUI Mode
To launch the graphical version:
```bash
python instad.py
```

Enter a URL from any supported site and start downloading instantly.  
If no display is detected (e.g. Termux), it automatically switches to terminal mode.

### Terminal Mode
If running on a system without a graphical interface, the tool will start in text mode automatically.  
Follow the on-screen instructions to select download type, format, and quality.

### Command-Line (Legacy)
For older versions:
```bash
unset DISPLAY
python instad.py tech_burner 10
```
## Reset GUI
```bash
export DISPLAY=:0
```
---

## Instagram Login (Optional)
If you encounter rate limits or want to download from private accounts you follow, create a session file:
```bash
instaloader -l your_username
```
or use this one-liner:
```bash
python -c "from instaloader import Instaloader; L=Instaloader(); L.login(input('Username: '), input('Password: ')); L.save_session_to_file()"
```
The script will automatically detect and use your saved session file (named `session-your_username`) when present.

---

## Output
All downloaded media is stored in the folder where the script is located (or the custom directory selected in the GUI).

---

## License
This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments
- [Instaloader](https://instaloader.github.io/) : Instagram media extraction  
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) : Multi-platform downloader  
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) : Modern GUI toolkit for Python

---

## Contributing
Contributions, suggestions, and feature ideas are always welcome.  
Open an issue or submit a pull request on [GitHub](https://github.com/debojitsantra/instad).

---

## Disclaimer
This tool is intended for personal, educational, and fair-use purposes only.  
Please respect creators rights and platform terms of service when downloading content.

---

## Author
[Debojit Santra](https://github.com/debojitsantra)
