import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import yt_dlp

class MediaDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Media Downloader")
        self.root.geometry("480x360")
        self.root.resizable(False, False)

        # Variables
        self.url_var = tk.StringVar()
        self.save_path = tk.StringVar(value=os.getcwd())
        self.quality_var = tk.StringVar(value="Best")

        # --- UI Layout ---
        tk.Label(root, text="Enter Media URL:", font=("Arial", 12)).pack(pady=10)
        tk.Entry(root, textvariable=self.url_var, width=50).pack(pady=5)

        tk.Label(root, text="Save Folder:", font=("Arial", 12)).pack(pady=5)
        path_frame = tk.Frame(root)
        path_frame.pack()
        tk.Entry(path_frame, textvariable=self.save_path, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(path_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)

        tk.Label(root, text="Select Quality:", font=("Arial", 12)).pack(pady=5)
        quality_options = ["Audio Only (mp3)", "360p", "480p", "720p", "1080p", "Best"]
        ttk.Combobox(root, textvariable=self.quality_var, values=quality_options, state="readonly", width=25).pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=15)

        self.status_label = tk.Label(root, text="", font=("Arial", 10), fg="blue")
        self.status_label.pack()

        tk.Button(root, text="Download", command=self.start_download, width=20, bg="#0078D7", fg="white").pack(pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.set(folder)

    def start_download(self):
        url = self.url_var.get().strip()
        save_dir = self.save_path.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return
        if not os.path.isdir(save_dir):
            messagebox.showerror("Error", "Invalid save folder.")
            return

        self.status_label.config(text="Starting download...")
        self.progress['value'] = 0

        thread = threading.Thread(target=self.download_media, args=(url, save_dir, self.quality_var.get()))
        thread.start()

    def get_format(self, quality):
        """Map dropdown quality to yt-dlp format string."""
        formats = {
            "Audio Only (mp3)": "bestaudio/best",
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "Best": "bestvideo+bestaudio/best"
        }
        return formats.get(quality, "bestvideo+bestaudio/best")

    def download_media(self, url, save_dir, quality):
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded = d.get('downloaded_bytes', 0)
                    if total:
                        percent = downloaded / total * 100
                        self.progress['value'] = percent
                    self.status_label.config(text=f"Downloading... {int(self.progress['value'])}%")
                elif d['status'] == 'finished':
                    self.progress['value'] = 100
                    self.status_label.config(text="Download complete!")

            ydl_opts = {
                'outtmpl': os.path.join(save_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'noprogress': True,
                'format': self.get_format(quality),
            }

            # Convert to MP3 if audio only
            if quality == "Audio Only (mp3)":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            messagebox.showinfo("Success", "Download completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")
            self.status_label.config(text="Error occurred.")

# --- Run GUI ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MediaDownloaderApp(root)
    root.mainloop()
