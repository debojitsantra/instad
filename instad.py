import os
import re
import threading
import yt_dlp
import instaloader
from tqdm import tqdm
import sys
try:
    import customtkinter as ctk
    from tkinter import messagebox
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False



# Site Detection

def detect_site(url):
    url = url.lower()
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "soundgasm.net" in url:
        return "soundgasm"
    elif "instagram.com" in url:
        if re.search(r"instagram\\.com/[^/]+/?$", url):
            return "instagram_profile"
        return "instagram_post"
    elif "facebook.com" in url:
        return "facebook"
    elif "reddit.com" in url:
        return "reddit"
    else:
        return "unknown"



# Downloader Functions

def download_youtube(url, save_dir, quality, log_callback=print):
    quality_map = {
        "Audio Only (mp3)": "bestaudio/best",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "Best": "bestvideo+bestaudio/best"
    }

    fmt = quality_map.get(quality, "bestvideo+bestaudio/best")
    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
        "format": fmt,
        "quiet": True
    }

    if quality == "Audio Only (mp3)":
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    log_callback(f"▶ Downloading YouTube in {quality} quality...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    log_callback("YouTube download complete!\n")


def download_best(url, save_dir, log_callback=print):
    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    log_callback("Download complete!\n")


def download_soundgasm(url, save_dir, log_callback=print):
    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True
    }
    log_callback("Downloading Soundgasm audio (auto converting to MP3)...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    log_callback("Soundgasm audio saved as MP3!\n")


def download_instagram_profile(username, save_dir, log_callback=print):
    loader = instaloader.Instaloader(dirname_pattern=save_dir)
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        log_callback(f"The account '{username}' does not exist.")
        return
    except instaloader.exceptions.ConnectionException:
        log_callback("Connection error. Check your internet.")
        return

    if profile.is_private:
        log_callback(f"🔒 The profile '{username}' is private. Cannot download.")
        return

    total_posts = profile.mediacount
    log_callback(f"'{username}' has {total_posts} posts.")
    try:
        limit = int(input("How many posts to download? (enter a number): "))
    except ValueError:
        log_callback("Invalid input.")
        return

    count = 0
    posts = profile.get_posts()
    with tqdm(total=min(limit, total_posts), ncols=80) as pbar:
        for post in posts:
            if count >= limit:
                break
            loader.download_post(post, target=os.path.join(save_dir, username))
            count += 1
            pbar.update(1)
    log_callback("Profile media downloaded!\n")



# Terminal Interface (TUI)

def run_tui():
    print("\n=== Universal Media Downloader (TUI Mode) ===")
    url = input("Enter media URL: ").strip()
    save_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(save_dir, exist_ok=True)

    site = detect_site(url)
    print(f"Detected site: {site}")

    try:
        if site == "youtube":
            print("\nSelect quality:")
            print("1) Audio Only (mp3)")
            print("2) 360p")
            print("3) 480p")
            print("4) 720p")
            print("5) 1080p")
            print("6) Best")
            q_choice = input("Enter choice: ").strip()
            q_map = {
                "1": "Audio Only (mp3)",
                "2": "360p",
                "3": "480p",
                "4": "720p",
                "5": "1080p",
                "6": "Best"
            }
            quality = q_map.get(q_choice, "Best")
            download_youtube(url, save_dir, quality)
        elif site == "soundgasm":
            download_soundgasm(url, save_dir)
        elif site in ("facebook", "reddit", "instagram_post"):
            download_best(url, save_dir)
        elif site == "instagram_profile":
            username = url.split("/")[-1] or url.split("/")[-2]
            download_instagram_profile(username, save_dir)
        else:
            print("Unsupported site or invalid URL.")
    except Exception as e:
        print(f"Error: {e}")



# GUI

class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Universal Media Downloader")
        self.geometry("620x480")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.url_var = ctk.StringVar()
        self.save_path = os.path.join(os.getcwd(), "downloads")
        self.quality_var = ctk.StringVar(value="Best")

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Media URL", font=("Arial", 14)).pack(pady=(15, 5))
        ctk.CTkEntry(self, textvariable=self.url_var, width=500, height=35).pack(pady=5)
        ctk.CTkLabel(self, text=f"Save Folder: {self.save_path}", font=("Arial", 12)).pack(pady=5)
        ctk.CTkLabel(self, text="Quality (YouTube only):", font=("Arial", 12)).pack(pady=5)

        options = ["Audio Only (mp3)", "360p", "480p", "720p", "1080p", "Best"]
        self.quality_menu = ctk.CTkOptionMenu(self, variable=self.quality_var, values=options)
        self.quality_menu.pack(pady=5)

        ctk.CTkButton(self, text="Start Download", command=self.start_download, width=200, height=40).pack(pady=10)
        self.log_box = ctk.CTkTextbox(self, width=550, height=220, font=("Consolas", 11))
        self.log_box.pack(pady=10)
        self.log("Ready.\n")

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return
        self.log(f"Detected site: {detect_site(url)}")
        thread = threading.Thread(target=self.download_handler, args=(url,))
        thread.start()

    def download_handler(self, url):
        site = detect_site(url)
        try:
            if site == "youtube":
                download_youtube(url, self.save_path, self.quality_var.get(), self.log)
            elif site == "soundgasm":
                download_soundgasm(url, self.save_path, self.log)
            elif site in ("facebook", "reddit", "instagram_post"):
                download_best(url, self.save_path, self.log)
            elif site == "instagram_profile":
                username = url.split("/")[-1] or url.split("/")[-2]
                download_instagram_profile(username, self.save_path, self.log)
            else:
                self.log("Unsupported site or invalid URL.")
        except Exception as e:
            self.log(f"Error: {e}\n")



# Entry Point

if __name__ == "__main__":
    if not GUI_AVAILABLE or not os.environ.get("DISPLAY"):
        run_tui()
    else:
        app = DownloaderApp()
        app.mainloop()