

**Instad** is a Python-based media downloader that allows you to easily fetch photos, videos, and audio from multiple platforms ” including **Instagram**, **YouTube**, **Soundgasm**, **Reddit**, and **Facebook**.  
It uses `instaloader` and `yt-dlp` under the hood to deliver reliable, high-quality downloads.

---

##  **Features**
- Download public Instagram posts and profiles  
- YouTube downloads with quality selection (Audio, 360p, 1080p, Best)  
- Soundgasm downloads automatically converted to MP3  
- Facebook and Reddit media downloads at best available quality  
- Detects private Instagram profiles and handles them safely  
- Modern GUI built with `customtkinter`

---

## **Prerequisites**
- Python 3.8 or later  
- `ffmpeg` (for media conversion)  
- Required Python libraries listed in `requirements.txt`

---

##  **Installation**

1. Clone the repository or download the latest release.  
2. Navigate into the project folder.  
3. Install all dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

##  **Usage**

### GUI Mode
To launch the graphical version:
```bash
python instad.py
```
- Termux Only
```bash
termux-x11 :0 & python instad.py
```
Enter a URL from any supported site and start downloading instantly.  
If no display is detected (e.g. Termux), it automatically switches to terminal mode.

### Command-Line Mode (Legacy)
For older versions:
```bash
python instad.py account_name limit
```
Example:
```bash
python instad.py mehdi_sadaghdar 10
```
Downloads the 10 latest public posts from the specified account.

---

## **Output**
All downloaded media is stored in the folder where the script is located (or `/downloads` if running from GUI mode).

---

## **License**
This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## **Acknowledgments**
- [Instaloader](https://instaloader.github.io/) Instagram media extraction  
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)  Multi-platform downloader  
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)  Modern GUI toolkit for Python

---

## **Contributing**
Contributions, suggestions, and feature ideas are always welcome.  
Open an issue or submit a pull request on [GitHub](https://github.com/debojitsantra/instad).

---

## **Disclaimer**
This tool is intended for **personal, educational, and fair-use purposes only**.  
Please respect creators rights and platform terms of service when downloading content.

---

##  **Author**
**[Debojit Santra](https://github.com/debojitsantra)**
