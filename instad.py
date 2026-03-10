import os
import re
import threading
import yt_dlp
import instaloader
from tqdm import tqdm
import sys

# Try importing GUI modules
try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False


def detect_site(url):
    url = url.lower()
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "soundgasm.net" in url:
        return "soundgasm"
    elif "instagram.com" in url:
        if re.search(r"instagram\.com/[^/]+/?$", url):
            return "instagram_profile"
        return "instagram_post"
    elif "facebook.com" in url:
        return "facebook"
    elif "reddit.com" in url:
        return "reddit"
    else:
        return "unknown"


def download_youtube(url, save_dir, quality, progress_callback=None, log_callback=print):
    quality_map = {
        "Audio Only (mp3)": "bestaudio/best",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "Best": "bestvideo+bestaudio/best"
    }
    fmt = quality_map.get(quality, "bestvideo+bestaudio/best")

    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                progress_callback(downloaded / total * 100)
        elif d['status'] == 'finished' and progress_callback:
            progress_callback(100)

    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
        "format": fmt,
        "quiet": True,
        "progress_hooks": [hook],
        "extractor_args": {"youtube": {"player_client": ["default"]}}
    }

    if quality == "Audio Only (mp3)":
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    log_callback(f"Downloading YouTube in {quality} quality...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    log_callback("YouTube download complete.")


def download_best(url, save_dir, progress_callback=None, log_callback=print):
    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                progress_callback(downloaded / total * 100)
        elif d['status'] == 'finished' and progress_callback:
            progress_callback(100)

    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "quiet": True,
        "progress_hooks": [hook]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    log_callback("Download complete.")


def download_soundgasm(url, save_dir, progress_callback=None, log_callback=print):
    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                progress_callback(downloaded / total * 100)
        elif d['status'] == 'finished' and progress_callback:
            progress_callback(100)

    ydl_opts = {
        "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "progress_hooks": [hook]
    }

    log_callback("Downloading Soundgasm audio (auto converting to MP3)...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    log_callback("Soundgasm audio saved as MP3.")


def load_instagram_session(loader, log_callback=print):
    """Automatically loads saved Instagram session if available."""
    try:
        session_files = [f for f in os.listdir('.') if f.startswith("session-")]
    except Exception:
        return False
    if session_files:
        try:
            session_file = session_files[0]
            username = session_file.replace("session-", "")
            loader.load_session_from_file(username)
            log_callback(f"Loaded Instagram session from {session_file}")
            return True
        except Exception as e:
            log_callback(f"Failed to load session: {e}")
    return False


def download_instagram_profile(username, save_dir, log_callback=print):
    loader = instaloader.Instaloader(dirname_pattern=save_dir)
    session_loaded = load_instagram_session(loader, log_callback)

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        log_callback(f"The account '{username}' does not exist.")
        return
    except instaloader.exceptions.ConnectionException:
        log_callback("Connection error. Check your internet.")
        return

    if profile.is_private and not session_loaded:
        log_callback(f"The profile '{username}' is private. Login required.")
        return

    total_posts = profile.mediacount
    log_callback(f"'{username}' has {total_posts} posts.")

    try:
        limit_str = input("How many posts to download? (enter a number): ").strip()
        limit = int(limit_str)
    except (ValueError, EOFError):
        log_callback("Invalid input.")
        return

    count = 0
    posts = profile.get_posts()
    with tqdm(total=min(limit, total_posts), ncols=80) as pbar:
        for post in posts:
            if count >= limit:
                break
            try:
                loader.download_post(post, target=os.path.join(save_dir, username))
            except Exception as e:
                log_callback(f"Skipped post: {e}")
            count += 1
            pbar.update(1)
    log_callback("Profile media downloaded.")


def extract_instagram_username(url):
    """Reliably extract username from Instagram profile URL."""
    url = url.rstrip("/")
    parts = url.split("/")
    # Filter out empty strings
    parts = [p for p in parts if p]
    # Last non-empty part after stripping protocol/domain
    for part in reversed(parts):
        if "instagram.com" not in part:
            return part
    return parts[-1]


def run_tui():
    print("\n=== Instad (TUI Mode) ===")

    default_dir = os.path.join(os.getcwd(), "downloads")
    print(f"Default download folder: {default_dir}")
    custom_dir = input("Enter custom download folder (or press Enter to use default): ").strip()

    if custom_dir:
        save_dir = os.path.expanduser(custom_dir)
    else:
        save_dir = default_dir

    os.makedirs(save_dir, exist_ok=True)
    print(f"Download directory set to: {save_dir}\n")

    url = input("Enter media URL: ").strip()
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
            username = extract_instagram_username(url)
            download_instagram_profile(username, save_dir)
        else:
            print("Unsupported site or invalid URL.")
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"Error: {e}")


if GUI_AVAILABLE:
    class DownloaderApp(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Instad")
            self.geometry("640x520")
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")

            self.url_var = ctk.StringVar()
            self.save_path = os.path.join(os.getcwd(), "downloads")
            self.quality_var = ctk.StringVar(value="Best")

            self._build_ui()

        def _build_ui(self):
            ctk.CTkLabel(self, text="Media URL", font=("Arial", 14)).pack(pady=(15, 5))
            ctk.CTkEntry(self, textvariable=self.url_var, width=500, height=35).pack(pady=5)

            path_frame = ctk.CTkFrame(self)
            path_frame.pack(pady=5)
            ctk.CTkLabel(path_frame, text="Save Folder:", font=("Arial", 12)).pack(side="left", padx=5)
            ctk.CTkButton(path_frame, text="Change", command=self.change_directory, width=80).pack(side="right", padx=5)
            self.path_label = ctk.CTkLabel(path_frame, text=self.save_path, font=("Arial", 11))
            self.path_label.pack(side="left", padx=5)

            ctk.CTkLabel(self, text="Quality (YouTube only):", font=("Arial", 12)).pack(pady=5)
            options = ["Audio Only (mp3)", "360p", "480p", "720p", "1080p", "Best"]
            self.quality_menu = ctk.CTkOptionMenu(self, variable=self.quality_var, values=options)
            self.quality_menu.pack(pady=5)

            self.progress = ctk.CTkProgressBar(self, width=500)
            self.progress.set(0)
            self.progress.pack(pady=10)

            ctk.CTkButton(self, text="Start Download", command=self.start_download, width=200, height=40).pack(pady=10)

            self.log_box = ctk.CTkTextbox(self, width=580, height=220, font=("Consolas", 11))
            self.log_box.pack(pady=10)
            self.log("Ready.")

        def log(self, message):
            self.log_box.insert("end", str(message) + "\n")
            self.log_box.see("end")

        def change_directory(self):
            new_dir = filedialog.askdirectory()
            if new_dir:
                self.save_path = new_dir
                self.path_label.configure(text=self.save_path)
                self.log(f"Download folder changed to: {self.save_path}")

        def start_download(self):
            url = self.url_var.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter a URL.")
                return
            os.makedirs(self.save_path, exist_ok=True)
            self.progress.set(0)
            self.log(f"Detected site: {detect_site(url)}")
            thread = threading.Thread(target=self.download_handler, args=(url,), daemon=True)
            thread.start()

        def update_progress(self, percent):
            self.progress.set(percent / 100)

        def download_handler(self, url):
            site = detect_site(url)
            try:
                if site == "youtube":
                    download_youtube(url, self.save_path, self.quality_var.get(), self.update_progress, self.log)
                elif site == "soundgasm":
                    download_soundgasm(url, self.save_path, self.update_progress, self.log)
                elif site in ("facebook", "reddit", "instagram_post"):
                    download_best(url, self.save_path, self.update_progress, self.log)
                elif site == "instagram_profile":
                    username = extract_instagram_username(url)
                    download_instagram_profile(username, self.save_path, self.log)
                else:
                    self.log("Unsupported site or invalid URL.")
            except Exception as e:
                self.log(f"Error: {e}")


if __name__ == "__main__":
    import platform
    on_linux = platform.system() == "Linux"
    has_display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")

    if not GUI_AVAILABLE or (on_linux and not has_display):
        run_tui()
    else:
        try:
            app = DownloaderApp()
            app.mainloop()
        except Exception:
            run_tui()  