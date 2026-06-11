import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import ctypes
import ctypes.wintypes
from urllib.parse import urlparse
import yt_dlp

try:
    import customtkinter as ctk
    from tkinter import PhotoImage, filedialog, messagebox
    from PIL import Image

    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False



APP_NAME = "Instad"
VERSION = "v1.2.0.0"
DEFAULT_FILENAME_PATTERN = "%(extractor)s/%(title).180s [%(id)s].%(ext)s"
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


if sys.platform.startswith('win'):
    APP_DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), APP_NAME)
elif sys.platform.startswith('darwin'):
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', APP_NAME)
else:
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.config', APP_NAME)

CONFIG_DIR = os.path.join(APP_DATA_DIR, "config")
COOKIES_FILE_PATH = os.path.join(CONFIG_DIR, "cookies.txt")

COLORS = {
    "window": ("#F2F2F7", "#07080C"),
    "surface": ("#FFFFFF", "#17181F"),
    "surface_soft": ("#F9F9FB", "#20222B"),
    "surface_muted": ("#F2F2F7", "#262934"),
    "border": ("#DADAE0", "#343844"),
    "border_soft": ("#E5E5EA", "#2A2D37"),
    "shadow": ("#D9DDE8", "#05060A"),
    "text": ("#000000", "#F5F5F7"),
    "text_secondary": ("#3C3C43", "#C7C7CC"),
    "accent": ("#007AFF", "#0A84FF"),
    "accent_hover": ("#0062CC", "#409CFF"),
    "accent_soft": ("#E9F2FF", "#112B4E"),
    "input": ("#F9F9FB", "#11131A"),
    "dropdown_hover": ("#E9F2FF", "#253A55"),
}


def _abgr_from_hex(hex_color, alpha):
    color = hex_color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return (alpha << 24) | (blue << 16) | (green << 8) | red


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def strip_ansi(text):
    return ANSI_ESCAPE_PATTERN.sub("", str(text))


def available_js_runtimes():
    system_deno = shutil.which("deno")
    if system_deno:
        return {"deno": {"path": system_deno}}
    return {}


def is_ejs_warning(message):
    lower_message = strip_ansi(message).lower()
    return any(
        marker in lower_message
        for marker in (
            "signature solving failed",
            "challenge solving failed",
            "supported javascript runtime",
            "ejs",
        )
    )


class YtdlpGuiLogger:
    def __init__(self, log_callback=print, run_state=None):
        self.log_callback = log_callback
        self.run_state = run_state if run_state is not None else {"warnings": [], "errors": []}

    def debug(self, message):
        if isinstance(message, str) and message.startswith("[debug]"):
            return
        self.log_callback(strip_ansi(message))

    def info(self, message):
        self.log_callback(strip_ansi(message))

    def warning(self, message):
        clean_message = strip_ansi(message)
        self.run_state["warnings"].append(clean_message)
        self.log_callback(f"Warning: {clean_message}")

    def error(self, message):
        clean_message = strip_ansi(message)
        self.run_state["errors"].append(clean_message)
        self.log_callback(f"Error: {clean_message}")

FORMAT_PRESETS = {
    "Best video + audio": {
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
    },
    "Best single file": {
        "format": "b",
    },
    "Audio only (original)": {
        "format": "ba/b",
    },
    "Audio only (mp3)": {
        "format": "ba/b",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    },
    "Video up to 1080p": {
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
    },
    "Video up to 720p": {
        "format": "bv*[height<=720]+ba/b[height<=720]/b",
        "merge_output_format": "mp4",
    },
    "Video up to 480p": {
        "format": "bv*[height<=480]+ba/b[height<=480]/b",
        "merge_output_format": "mp4",
    },
    "Video up to 1440p": {
        "format": "bv*[height<=1440]+ba/b[height<=1440]/b",
        "merge_output_format": "mp4",
    },
    "Video up to 2160p (4K)": {
        "format": "bv*[height<=2160]+ba/b[height<=2160]/b",
        "merge_output_format": "mp4",
    },
    "Highest quality video only": {
        "format": "bv*",
    },
    "Audio only (Opus)": {
        "format": "ba*[ext=opus]/ba*",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
            }
        ],
    },
}


def detect_site(url):
    host = urlparse(url.strip()).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return "unknown"
    return host


def make_progress_hook(progress_callback=None, log_callback=print, phase_callback=None):
    def hook(data):
        status = data.get("status")
        if status == "downloading":
            if phase_callback:
                phase_callback("Downloading")
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            if total and progress_callback:
                progress_callback(downloaded / total * 100)

            speed = data.get("_speed_str", "").strip()
            eta = data.get("_eta_str", "").strip()
            filename = os.path.basename(data.get("filename") or "")
            if filename and log_callback:
                detail = f"Downloading {filename}"
                if speed:
                    detail += f" | {speed}"
                if eta:
                    detail += f" | ETA {eta}"
                log_callback(detail)

        elif status == "finished":
            if progress_callback:
                progress_callback(100)
            if phase_callback:
                phase_callback("Processing")
            if log_callback:
                filename = os.path.basename(data.get("filename") or "media")
                log_callback(f"Finished: {filename}")

    return hook


def make_postprocessor_hook(progress_callback=None, log_callback=print, phase_callback=None):
    def hook(data):
        status = data.get("status")
        postprocessor = data.get("postprocessor") or "post-processing"
        if status in {"started", "processing"}:
            if phase_callback:
                phase_callback("Post-processing")
            if progress_callback:
                progress_callback(100)
            if log_callback:
                log_callback(f"Post-processing: {postprocessor}")
        elif status == "finished":
            if progress_callback:
                progress_callback(100)
            if phase_callback:
                phase_callback("Finished")
            if log_callback:
                log_callback(f"Post-processing complete: {postprocessor}")

    return hook


def build_ydl_options(
    save_dir,
    format_preset,
    filename_pattern=DEFAULT_FILENAME_PATTERN,
    download_playlist=True,
    write_subtitles=False,
    write_thumbnail=False,
    cookies_text="",
    cookie_file=None,
    progress_callback=None,
    log_callback=print,
    phase_callback=None,
    run_state=None,
):
    preset = FORMAT_PRESETS.get(format_preset, FORMAT_PRESETS["Best video + audio"])
    ydl_opts = {
        "outtmpl": os.path.join(save_dir, filename_pattern),
        "format": preset["format"],
        "quiet": True,
        "noprogress": True,
        "ignoreerrors": False,
        "no_warnings": True,
        "logger": YtdlpGuiLogger(log_callback, run_state),
        "progress_hooks": [make_progress_hook(progress_callback, log_callback, phase_callback)],
        "postprocessor_hooks": [make_postprocessor_hook(progress_callback, log_callback, phase_callback)],
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "js_runtimes": available_js_runtimes(),
        "remote_components": ["ejs:npm", "ejs:github"],
        "noplaylist": not download_playlist,
        "writesubtitles": write_subtitles,
        "writeautomaticsub": write_subtitles,
        "writethumbnail": write_thumbnail,
    }

    if "merge_output_format" in preset:
        ydl_opts["merge_output_format"] = preset["merge_output_format"]
    if "postprocessors" in preset:
        ydl_opts["postprocessors"] = preset["postprocessors"]

    cookie_header = normalize_cookie_header(cookies_text)
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file
    elif cookie_header:
        ydl_opts["http_headers"] = {"Cookie": cookie_header}

    return ydl_opts


def normalize_cookie_header(cookies_text):
    text = cookies_text.strip()
    if not text or looks_like_netscape_cookie_file(text):
        return ""
    if text.lower().startswith("cookie:"):
        text = text.split(":", 1)[1].strip()
    return " ".join(text.split())


def looks_like_netscape_cookie_file(cookies_text):
    text = cookies_text.strip()
    if not text:
        return False
    if "Netscape HTTP Cookie File" in text:
        return True
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if len(line.split("\t")) >= 7:
            return True
    return False


def write_temp_cookie_file(cookies_text):
    temp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".cookies.txt", encoding="utf-8")
    try:
        temp.write(cookies_text.strip())
        temp.write("\n")
        return temp.name
    finally:
        temp.close()


def download_with_ytdlp(
    urls,
    save_dir,
    format_preset="Best video + audio",
    filename_pattern=DEFAULT_FILENAME_PATTERN,
    download_playlist=True,
    write_subtitles=False,
    write_thumbnail=False,
    cookies_text="",
    progress_callback=None,
    log_callback=print,
    phase_callback=None,
):
    clean_urls = [url.strip() for url in urls if url.strip()]
    if not clean_urls:
        raise ValueError("Enter at least one URL.")

    os.makedirs(save_dir, exist_ok=True)
    log_callback(f"Saving to: {save_dir}")
    log_callback(f"Format: {format_preset}")
    if not shutil.which("deno"):
        log_callback(
            "Warning: Deno is not installed. YouTube may fail signature/challenge solving."
        )
    cookie_file = None
    run_state = {"warnings": [], "errors": []}
    if cookies_text.strip():
        if looks_like_netscape_cookie_file(cookies_text):
            cookie_file = write_temp_cookie_file(cookies_text)
            log_callback("Using pasted cookies.txt data.")
        else:
            log_callback("Using pasted Cookie header.")

    try:
        ydl_opts = build_ydl_options(
            save_dir=save_dir,
            format_preset=format_preset,
            filename_pattern=filename_pattern,
            download_playlist=download_playlist,
            write_subtitles=write_subtitles,
            write_thumbnail=write_thumbnail,
            cookies_text=cookies_text,
            cookie_file=cookie_file,
            progress_callback=progress_callback,
            log_callback=log_callback,
            phase_callback=phase_callback,
            run_state=run_state,
        )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.download(clean_urls)
        except Exception as exc:
            if any(is_ejs_warning(message) for message in run_state["warnings"]):
                raise RuntimeError(
                    "YouTube challenge solving failed. Install Deno, restart Instad, update yt-dlp, "
                    "then retry this download."
                ) from exc
            raise
        if result:
            raise RuntimeError(f"yt-dlp failed with exit code {result}.")
    finally:
        if cookie_file:
            try:
                os.unlink(cookie_file)
            except OSError:
                pass

    log_callback("All queued downloads finished.")


def run_tui():
    print(f"\n=== {APP_NAME} {VERSION} TUI ===")
    print("Paste any URL supported by yt-dlp. Add multiple URLs separated by commas.")

    default_dir = os.path.join(os.getcwd(), "downloads")
    custom_dir = input(f"Save folder [{default_dir}]: ").strip()
    save_dir = os.path.expanduser(custom_dir) if custom_dir else default_dir

    url_text = input("URL(s): ").strip()
    urls = [url.strip() for url in url_text.split(",")]

    print("\nFormat:")
    presets = list(FORMAT_PRESETS)
    for index, name in enumerate(presets, start=1):
        print(f"{index}) {name}")
    choice = input("Choose format [1]: ").strip()
    try:
        format_preset = presets[int(choice) - 1] if choice else presets[0]
    except (ValueError, IndexError):
        format_preset = presets[0]

    playlist_answer = input("Download playlists when present? [Y/n]: ").strip().lower()
    download_playlist = playlist_answer not in {"n", "no"}

    try:
        download_with_ytdlp(
            urls=urls,
            save_dir=save_dir,
            format_preset=format_preset,
            download_playlist=download_playlist,
        )
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as exc:
        print(f"Error: {exc}")


if GUI_AVAILABLE:

    class DownloaderApp(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title(f"{APP_NAME} {VERSION}")
            self.geometry("980x720")
            self.minsize(880, 640)
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self._set_window_icon()

            self.save_path = os.path.join(os.getcwd(), "downloads")
            self.url_text = None
            self.path_label = None
            self.log_box = None
            self.progress = None
            self.status_label = None
            self.download_button = None
            self.queue_frame = None
            self.empty_queue_label = None
            self.download_jobs = {}
            self.job_counter = 0

            self.format_var = ctk.StringVar(value="Best video + audio")
            self.filename_pattern_var = ctk.StringVar(value=DEFAULT_FILENAME_PATTERN)
            self.playlist_var = ctk.BooleanVar(value=True)
            self.subtitle_var = ctk.BooleanVar(value=False)
            self.thumbnail_var = ctk.BooleanVar(value=False)
            self.cookies_box = None
            self.opacity_var = ctk.DoubleVar(value=0.96)
            self.theme_var = ctk.StringVar(value="Dark")

            self._build_ui()
            self.update_idletasks()
            self._apply_frosted_glass(self.opacity_var.get())
            self._load_cookies() # Load cookies after UI is built
            self.protocol("WM_DELETE_WINDOW", self._on_closing) # Save cookies on app close

        def _font(self, size, weight="normal"):
            return ctk.CTkFont(family="SF Pro Display", size=size, weight=weight)

        def _set_window_icon(self):
            try:
                # Use .ico for Windows title bar, fallback to PhotoImage for others
                icon_path = resource_path(os.path.join("assets", "icon.ico"))
                if os.name == "nt":
                    self.iconbitmap(icon_path)
                
                icon_path_png = resource_path(os.path.join("assets", "icon.png"))
                self._icon_image = PhotoImage(file=icon_path_png if os.path.exists(icon_path_png) else icon_path)
                self.iconphoto(True, self._icon_image)

                # Create a CTkImage for CustomTkinter widgets to render the icon properly
                target_path = icon_path_png if os.path.exists(icon_path_png) else icon_path
                if os.path.exists(target_path):
                    pil_image = Image.open(target_path)
                    self._icon_image_ctk = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(58, 58)
                    )
            except Exception:
                pass

        def _style_window_chrome(self, window):
            if os.name != "nt":
                return
            try:
                window.update_idletasks()
                dark_mode = ctypes.c_int(1 if self.theme_var.get() == "Dark" else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.wintypes.HWND(window.winfo_id()),
                    ctypes.c_uint(20),
                    ctypes.byref(dark_mode),
                    ctypes.sizeof(dark_mode),
                )
            except Exception:
                pass

        def _glass_frame(self, parent, **kwargs):
            return ctk.CTkFrame(
                parent,
                corner_radius=20,
                border_width=1,
                border_color=COLORS["border"],
                fg_color=COLORS["surface"],
                **kwargs,
            )

        def _shadow_shell(self, parent, **grid_kwargs):
            shell = ctk.CTkFrame(parent, fg_color="transparent")
            shell.grid(**grid_kwargs)
            shell.grid_columnconfigure(0, weight=1)
            shell.grid_rowconfigure(0, weight=1)

            shadow = ctk.CTkFrame(shell, corner_radius=24, fg_color=COLORS["shadow"])
            shadow.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=(8, 0))

            card = self._glass_frame(shell)
            card.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=(0, 8))
            return card

        def _primary_button(self, parent, text, command, **kwargs):
            return ctk.CTkButton(
                parent,
                text=text,
                command=command,
                corner_radius=12,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="#FFFFFF",
                font=self._font(15, "bold"),
                **kwargs,
            )

        def _build_ui(self):
            self.configure(fg_color=COLORS["window"])

            shell = ctk.CTkFrame(self, fg_color=COLORS["window"])
            shell.pack(fill="both", expand=True, padx=26, pady=22)
            shell.grid_columnconfigure(0, weight=1)
            shell.grid_rowconfigure(1, weight=1)

            nav = ctk.CTkFrame(
                shell,
                corner_radius=20,
                fg_color=COLORS["surface"],
                border_width=1,
                border_color=COLORS["border_soft"],
            )
            nav.grid(row=0, column=0, sticky="ew", pady=(0, 18))
            nav.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                nav,
                text="Instad",
                font=self._font(20, "bold"),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 0))
            ctk.CTkLabel(
                nav,
                text="A yt-dlp gui",
                text_color=COLORS["text_secondary"],
                anchor="w",
                font=self._font(14),
            ).grid(row=1, column=0, sticky="w", padx=24, pady=(2, 16))

            self.status_label = ctk.CTkLabel(
                nav,
                text="Ready",
                corner_radius=12,
                fg_color=COLORS["surface_muted"],
                text_color=COLORS["accent"],
                font=self._font(14, "bold"),
                width=130,
                height=38,
            )
            self.status_label.grid(row=0, column=1, rowspan=2, padx=24, pady=18, sticky="e")

            self.tabs = ctk.CTkTabview(
                shell,
                corner_radius=20,
                segmented_button_selected_color=COLORS["accent"],
                segmented_button_selected_hover_color=COLORS["accent_hover"],
                segmented_button_unselected_color=COLORS["surface_muted"],
                segmented_button_unselected_hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                fg_color=COLORS["surface"],
                border_width=1,
                border_color=COLORS["border_soft"],
            )
            self.tabs.grid(row=1, column=0, sticky="nsew")
            download_tab = self.tabs.add("Download")
            settings_tab = self.tabs.add("Settings")
            activity_tab = self.tabs.add("Activity")

            self._build_download_tab(download_tab)
            self._build_settings_tab(settings_tab)
            self._build_activity_tab(activity_tab)

        def _build_download_tab(self, parent):
            parent.configure(fg_color=COLORS["surface"])
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(1, weight=1)

            header = self._glass_frame(parent)
            header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
            header.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                header,
                text="Download",
                font=self._font(28, "bold"),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 0))
            ctk.CTkLabel(
                header,
                text="Paste one URL per line.",
                text_color=COLORS["text_secondary"],
                wraplength=620,
                justify="left",
                anchor="w",
                font=self._font(14),
            ).grid(row=1, column=0, sticky="w", padx=22, pady=(4, 18))

            self._primary_button(
                header,
                text="+ Add Download",
                command=self.open_add_download_dialog,
                width=150,
                height=40,
            ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 22))

            queue_card = self._shadow_shell(parent, row=1, column=0, sticky="nsew", padx=18, pady=10)
            queue_card.grid_columnconfigure(0, weight=1)
            queue_card.grid_rowconfigure(1, weight=1)

            ctk.CTkLabel(
                queue_card,
                text="Queue",
                font=self._font(18, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 6))

            self.queue_frame = ctk.CTkScrollableFrame(
                queue_card,
                fg_color="transparent",
                scrollbar_button_color=COLORS["surface_muted"],
                scrollbar_button_hover_color=COLORS["accent_soft"],
            )
            self.queue_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
            self.queue_frame.grid_columnconfigure(0, weight=1)

            self.empty_queue_label = ctk.CTkLabel(
                self.queue_frame,
                text="No downloads yet. Add a URL to configure and start a download.",
                font=self._font(14),
                text_color=COLORS["text_secondary"],
                height=120,
            )
            self.empty_queue_label.grid(row=0, column=0, sticky="ew", padx=8, pady=20)

            self.progress = ctk.CTkProgressBar(
                queue_card,
                height=12,
                corner_radius=12,
                fg_color=COLORS["surface_muted"],
                progress_color=COLORS["accent"],
            )
            self.progress.set(0)
            self.progress.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 18))

            self.download_button = self._primary_button(
                queue_card,
                text="Add Download",
                command=self.open_add_download_dialog,
                height=46,
            )
            self.download_button.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 22))

        def _build_settings_tab(self, parent):
            parent.configure(fg_color=COLORS["surface"])
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(
                parent,
                fg_color=COLORS["surface"],
                scrollbar_button_color=COLORS["surface_muted"],
                scrollbar_button_hover_color=COLORS["accent_soft"],
            )
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            card = self._shadow_shell(scroll, row=0, column=0, sticky="ew", padx=18, pady=18)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                card,
                text="Settings",
                font=self._font(28, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(22, 14))

            checkbox_style = {
                "corner_radius": 8,
                "fg_color": COLORS["accent"],
                "hover_color": COLORS["accent_soft"],
                "border_color": COLORS["border"],
                "checkmark_color": "#FFFFFF",
                "text_color": COLORS["text"],
                "font": self._font(14),
            }

            ctk.CTkLabel(card, text="Appearance", text_color=COLORS["text_secondary"], font=self._font(14)).grid(
                row=1, column=0, sticky="w", padx=22, pady=(4, 8)
            )
            ctk.CTkSegmentedButton(
                card,
                values=["Dark", "Light"],
                variable=self.theme_var,
                command=self._set_theme,
                corner_radius=12,
                selected_color=COLORS["accent"],
                selected_hover_color=COLORS["accent_hover"],
                unselected_color=COLORS["surface_muted"],
                unselected_hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
            ).grid(row=1, column=1, sticky="ew", padx=(8, 22), pady=(4, 8))

            ctk.CTkCheckBox(
                card,
                text="Download playlists when a URL contains one",
                variable=self.playlist_var,
                **checkbox_style,
            ).grid(
                row=2, column=0, columnspan=2, sticky="w", padx=22, pady=8
            )
            ctk.CTkCheckBox(
                card,
                text="Save subtitles when available",
                variable=self.subtitle_var,
                **checkbox_style,
            ).grid(
                row=3, column=0, columnspan=2, sticky="w", padx=22, pady=8
            )
            ctk.CTkCheckBox(
                card,
                text="Save thumbnails when available",
                variable=self.thumbnail_var,
                **checkbox_style,
            ).grid(
                row=4, column=0, columnspan=2, sticky="w", padx=22, pady=8
            )

            cookie_label = ctk.CTkFrame(card, fg_color="transparent")
            cookie_label.grid(row=5, column=0, sticky="nw", padx=22, pady=(22, 8))
            ctk.CTkLabel(
                cookie_label,
                text="Cookies",
                text_color=COLORS["text_secondary"],
                font=self._font(14),
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkButton(
                cookie_label,
                text="i",
                command=self.open_readme,
                width=24,
                height=24,
                corner_radius=12,
                fg_color=COLORS["surface_muted"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(13, "bold"),
            ).grid(row=0, column=1, sticky="w", padx=(8, 0))
            self.cookies_box = ctk.CTkTextbox(
                card,
                height=112,
                corner_radius=12,
                border_width=1,
                border_color=COLORS["border"],
                fg_color=COLORS["input"],
                text_color=COLORS["text"],
                font=self._font(12),
            )
            self.cookies_box.grid(row=5, column=1, sticky="ew", padx=(8, 22), pady=(22, 8))
            ctk.CTkLabel(
                card,
                text="Paste a Netscape cookies.txt export or a raw Cookie header for age-restricted/private videos.",
                text_color=COLORS["text_secondary"],
                font=self._font(12),
                wraplength=520,
                justify="left",
            ).grid(row=6, column=0, columnspan=2, sticky="w", padx=22, pady=(0, 12))

            ctk.CTkLabel(card, text="Filename pattern", text_color=COLORS["text_secondary"], font=self._font(14)).grid(
                row=7, column=0, sticky="w", padx=22, pady=(12, 8)
            )
            ctk.CTkEntry(
                card,
                textvariable=self.filename_pattern_var,
                corner_radius=12,
                border_color=COLORS["border"],
                fg_color=COLORS["input"],
                text_color=COLORS["text"],
                font=self._font(13),
            ).grid(
                row=7, column=1, sticky="ew", padx=(8, 22), pady=(12, 8)
            )

            ctk.CTkLabel(card, text="Ui Transparency", text_color=COLORS["text_secondary"], font=self._font(14)).grid(
                row=8, column=0, sticky="w", padx=22, pady=(18, 8)
            )
            opacity_slider = ctk.CTkSlider(
                card,
                from_=0.72,
                to=1.0,
                variable=self.opacity_var,
                command=self._apply_frosted_glass,
                button_color=COLORS["accent"],
                button_hover_color=COLORS["accent_hover"],
                progress_color=COLORS["accent"],
                fg_color=COLORS["surface_muted"],
            )
            opacity_slider.grid(row=8, column=1, sticky="ew", padx=(8, 22), pady=(18, 8))

            self._primary_button(
                card,
                text="Update yt-dlp",
                command=self.update_ytdlp,
                height=42,
            ).grid(row=10, column=0, columnspan=2, sticky="ew", padx=22, pady=(4, 22))

        def _build_activity_tab(self, parent):
            parent.configure(fg_color=COLORS["surface"])
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(0, weight=1)

            card = self._shadow_shell(parent, row=0, column=0, sticky="nsew", padx=18, pady=18)
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(1, weight=1)

            ctk.CTkLabel(
                card,
                text="Activity",
                font=self._font(28, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, column=0, sticky="w", padx=22, pady=(22, 12))
            ctk.CTkButton(
                card,
                text="Clear",
                command=self.clear_activity,
                width=86,
                corner_radius=12,
                fg_color=COLORS["surface_muted"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(13, "bold"),
            ).grid(row=0, column=1, sticky="e", padx=22, pady=(22, 12))

            self.log_box = ctk.CTkTextbox(
                card,
                corner_radius=16,
                border_width=1,
                border_color=COLORS["border"],
                fg_color=COLORS["input"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(family="Consolas", size=12),
            )
            self.log_box.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=22, pady=(0, 22))
            self.log("Ready. Paste any URL supported by yt-dlp.")

        def open_add_download_dialog(self, initial_config=None):
            initial_config = initial_config or {}
            width = 620
            height = 610
            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - width) // 2
            y = self.winfo_y() + (self.winfo_height() - height) // 2

            dialog = ctk.CTkToplevel(self)
            dialog.title("Add Download")
            dialog.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
            dialog.minsize(560, 540)
            dialog.transient(self)
            dialog.grab_set()
            dialog.configure(fg_color=COLORS["surface"])
            self._style_window_chrome(dialog)
            dialog.grid_columnconfigure(0, weight=1)
            dialog.grid_rowconfigure(0, weight=1)

            save_dir_var = ctk.StringVar(value=initial_config.get("save_dir", self.save_path))
            format_var = ctk.StringVar(value=initial_config.get("format_preset", self.format_var.get()))
            filename_pattern_var = ctk.StringVar(
                value=initial_config.get("filename_pattern", self.filename_pattern_var.get())
            )
            playlist_var = ctk.BooleanVar(value=initial_config.get("download_playlist", self.playlist_var.get()))
            subtitle_var = ctk.BooleanVar(value=initial_config.get("write_subtitles", self.subtitle_var.get()))
            thumbnail_var = ctk.BooleanVar(value=initial_config.get("write_thumbnail", self.thumbnail_var.get()))

            body = ctk.CTkScrollableFrame(
                dialog,
                fg_color=COLORS["surface"],
                scrollbar_button_color=COLORS["surface_muted"],
                scrollbar_button_hover_color=COLORS["accent_soft"],
            )
            body.grid(row=0, column=0, sticky="nsew", padx=20, pady=(18, 0))
            body.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(body, text="Add Download", font=self._font(26, "bold"), text_color=COLORS["text"]).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
            )
            ctk.CTkLabel(body, text="URLs", font=self._font(14), text_color=COLORS["text_secondary"]).grid(
                row=1, column=0, columnspan=2, sticky="w"
            )
            url_box = ctk.CTkTextbox(
                body,
                height=105,
                corner_radius=16,
                border_width=1,
                border_color=COLORS["border"],
                fg_color=COLORS["input"],
                text_color=COLORS["text"],
                font=self._font(14),
            )
            url_box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 14))
            if initial_config.get("urls"):
                url_box.insert("1.0", "\n".join(initial_config["urls"]))

            ctk.CTkLabel(body, text="Save folder", font=self._font(14), text_color=COLORS["text_secondary"]).grid(
                row=3, column=0, sticky="w", pady=(4, 6)
            )
            ctk.CTkEntry(
                body,
                textvariable=save_dir_var,
                corner_radius=12,
                border_color=COLORS["border"],
                fg_color=COLORS["input"],
                text_color=COLORS["text"],
                font=self._font(13),
            ).grid(row=4, column=0, sticky="ew", pady=(0, 12))

            def choose_folder():
                folder = filedialog.askdirectory(parent=dialog)
                if folder:
                    save_dir_var.set(folder)

            self._primary_button(body, text="Browse", command=choose_folder, width=90).grid(
                row=4, column=1, sticky="e", padx=(10, 0), pady=(0, 12)
            )

            ctk.CTkLabel(body, text="Format", font=self._font(14), text_color=COLORS["text_secondary"]).grid(
                row=5, column=0, sticky="w", pady=(4, 6)
            )
            ctk.CTkOptionMenu(
                body,
                variable=format_var,
                values=list(FORMAT_PRESETS),
                corner_radius=12,
                fg_color=COLORS["surface_muted"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["accent_hover"],
                text_color=COLORS["text"],
                dropdown_fg_color=COLORS["surface"],
                dropdown_hover_color=COLORS["dropdown_hover"],
                dropdown_text_color=COLORS["text"],
            ).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 12))

            ctk.CTkLabel(body, text="Filename pattern", font=self._font(14), text_color=COLORS["text_secondary"]).grid(
                row=7, column=0, sticky="w", pady=(4, 6)
            )
            ctk.CTkEntry(
                body,
                textvariable=filename_pattern_var,
                corner_radius=12,
                border_color=COLORS["border"],
                fg_color=COLORS["input"],
                text_color=COLORS["text"],
                font=self._font(13),
            ).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 12))

            checkbox_style = {
                "corner_radius": 8,
                "fg_color": COLORS["accent"],
                "hover_color": COLORS["accent_soft"],
                "border_color": COLORS["border"],
                "checkmark_color": "#FFFFFF",
                "text_color": COLORS["text"],
                "font": self._font(14),
            }
            ctk.CTkCheckBox(body, text="Download playlist when present", variable=playlist_var, **checkbox_style).grid(
                row=9, column=0, columnspan=2, sticky="w", pady=6
            )
            ctk.CTkCheckBox(body, text="Save subtitles", variable=subtitle_var, **checkbox_style).grid(
                row=10, column=0, columnspan=2, sticky="w", pady=6
            )
            ctk.CTkCheckBox(body, text="Save thumbnails", variable=thumbnail_var, **checkbox_style).grid(
                row=11, column=0, columnspan=2, sticky="w", pady=(6, 14)
            )

            actions = ctk.CTkFrame(dialog, fg_color=COLORS["surface_muted"], corner_radius=0)
            actions.grid(row=1, column=0, sticky="ew")
            actions.grid_columnconfigure((0, 1), weight=1)

            def submit():
                urls = [url.strip() for url in url_box.get("1.0", "end").splitlines() if url.strip()]
                if not urls:
                    messagebox.showerror("Missing URL", "Paste at least one URL.", parent=dialog)
                    return
                config = {
                    "urls": urls,
                    "save_dir": save_dir_var.get().strip() or self.save_path,
                    "format_preset": format_var.get(),
                    "filename_pattern": filename_pattern_var.get().strip() or DEFAULT_FILENAME_PATTERN,
                    "download_playlist": playlist_var.get(),
                    "write_subtitles": subtitle_var.get(),
                    "write_thumbnail": thumbnail_var.get(),
                    "cookies_text": self.get_cookies_text(),
                }
                self.save_path = config["save_dir"]
                self.enqueue_download(config)
                dialog.destroy()

            self._primary_button(actions, text="Download", command=submit, height=38).grid(
                row=0, column=0, sticky="ew", padx=(20, 8), pady=16
            )
            ctk.CTkButton(
                actions,
                text="Cancel",
                command=dialog.destroy,
                corner_radius=12,
                fg_color=COLORS["surface"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(14, "bold"),
                height=38,
            ).grid(row=0, column=1, sticky="ew", padx=(8, 20), pady=16)

        def enqueue_download(self, config):
            self.job_counter += 1
            job_id = self.job_counter
            if self.empty_queue_label is not None:
                self.empty_queue_label.grid_forget()

            card = ctk.CTkFrame(
                self.queue_frame,
                corner_radius=16,
                border_width=1,
                border_color=COLORS["border"],
                fg_color=COLORS["surface_soft"],
            )
            card.grid(row=job_id, column=0, sticky="ew", padx=6, pady=8)
            card.grid_columnconfigure(1, weight=1)

            source = detect_site(config["urls"][0])
            title = config["urls"][0]
            if len(title) > 92:
                title = title[:89] + "..."

            icon_label = ctk.CTkLabel(
                card,
                text="",
                image=self._icon_image_ctk if hasattr(self, "_icon_image_ctk") else None,
                width=58,
                height=58,
                corner_radius=14,
                fg_color=COLORS["surface_muted"],
            )
            icon_label.grid(row=0, column=0, rowspan=3, padx=(16, 14), pady=16)

            title_label = ctk.CTkLabel(
                card,
                text=title,
                anchor="w",
                justify="left",
                font=self._font(14, "bold"),
                text_color=COLORS["text"],
                wraplength=560,
            )
            title_label.grid(row=0, column=1, sticky="ew", pady=(16, 2))
            meta_label = ctk.CTkLabel(
                card,
                text=f"{source} | {config['format_preset']}",
                anchor="w",
                font=self._font(12),
                text_color=COLORS["text_secondary"],
            )
            meta_label.grid(row=1, column=1, sticky="ew")

            progress = ctk.CTkProgressBar(
                card,
                height=8,
                corner_radius=8,
                fg_color=COLORS["surface_muted"],
                progress_color=COLORS["accent"],
            )
            progress.set(0)
            progress.grid(row=2, column=1, sticky="ew", pady=(10, 16))

            status = ctk.CTkLabel(
                card,
                text="Queued",
                width=120,
                anchor="e",
                font=self._font(13, "bold"),
                text_color=COLORS["accent"],
            )
            status.grid(row=0, column=2, sticky="e", padx=(14, 16), pady=(16, 0))

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.grid(row=1, column=2, rowspan=2, sticky="e", padx=(14, 16), pady=(8, 16))
            ctk.CTkButton(
                actions,
                text="Log",
                command=lambda: self.tabs.set("Activity"),
                width=68,
                corner_radius=12,
                fg_color=COLORS["surface"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(13, "bold"),
            ).grid(row=0, column=0, padx=(0, 8))
            open_button = ctk.CTkButton(
                actions,
                text="Open",
                command=lambda path=config["save_dir"]: self.open_folder(path),
                width=72,
                corner_radius=12,
                fg_color=COLORS["surface"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(13, "bold"),
            )
            open_button.grid(row=0, column=1, padx=(0, 8))
            retry_button = ctk.CTkButton(
                actions,
                text="Retry",
                command=lambda current_job_id=job_id: self.retry_download(current_job_id),
                width=72,
                corner_radius=12,
                fg_color=COLORS["surface"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(13, "bold"),
            )
            retry_button.grid(row=0, column=2)

            self.download_jobs[job_id] = {
                "config": config,
                "progress": progress,
                "status": status,
                "title": title_label,
                "open_button": open_button,
                "retry_button": retry_button,
            }

            self.log(f"Queued: {config['urls'][0]}")
            thread = threading.Thread(target=self.download_job_handler, args=(job_id,), daemon=True)
            thread.start()

        def retry_download(self, job_id):
            job = self.download_jobs.get(job_id)
            if not job:
                return
            self.log(f"Reopening download: {job['config']['urls'][0]}")
            self.open_add_download_dialog(job["config"])

        def update_job_progress(self, job_id, percent):
            job = self.download_jobs.get(job_id)
            if not job:
                return
            value = max(0, min(100, percent)) / 100
            job["progress"].set(value)
            self.progress.set(value)

        def update_job_status(self, job_id, status):
            job = self.download_jobs.get(job_id)
            if not job:
                return
            job["status"].configure(text=status)
            if status == "Failed":
                job["open_button"].grid_remove()
                job["retry_button"].grid_configure(row=0, column=1, padx=0)
            else:
                job["open_button"].grid(row=0, column=1, padx=(0, 8))
                job["retry_button"].grid_configure(row=0, column=2, padx=0)
            self.status_label.configure(text=status)

        def download_job_handler(self, job_id):
            job = self.download_jobs[job_id]
            config = job["config"]
            self._ui(self.update_job_status, job_id, "Downloading")
            try:
                self.safe_log(f"Detected source: {detect_site(config['urls'][0])}")
                download_with_ytdlp(
                    urls=config["urls"],
                    save_dir=config["save_dir"],
                    format_preset=config["format_preset"],
                    filename_pattern=config["filename_pattern"],
                    download_playlist=config["download_playlist"],
                    write_subtitles=config["write_subtitles"],
                    write_thumbnail=config["write_thumbnail"],
                    cookies_text=config.get("cookies_text", ""),
                    progress_callback=lambda percent: self._ui(self.update_job_progress, job_id, percent),
                    log_callback=self.safe_log,
                    phase_callback=lambda phase: self._ui(self.update_job_status, job_id, phase),
                )
                self._ui(self.update_job_progress, job_id, 100)
                self._ui(self.update_job_status, job_id, "Complete")
            except Exception as exc:
                self.safe_log(f"Error: {exc}")
                if config.get("cookies_text") and "cookies" in str(exc).lower():
                    self.safe_log(
                        "Cookie tip: paste fresh cookies in Settings, then press Retry to edit and start again."
                    )
                self._ui(self.update_job_status, job_id, "Failed")
            finally:
                self.safe_phase("Ready")

        def open_folder(self, path):
            try:
                if os.name == "nt":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
            except Exception as exc:
                self.log(f"Could not open folder: {exc}")

        def _load_cookies(self):
            """Loads cookies from the persistent cookies.txt file."""
            if os.path.exists(COOKIES_FILE_PATH):
                try:
                    with open(COOKIES_FILE_PATH, "r", encoding="utf-8") as f:
                        cookies_content = f.read()
                        if self.cookies_box:
                            self.cookies_box.delete("1.0", "end")
                            self.cookies_box.insert("1.0", cookies_content)
                except Exception as e:
                    self.log(f"Error loading cookies from {COOKIES_FILE_PATH}: {e}")

        def _save_cookies(self):
            """Saves cookies from the cookies_box to the persistent cookies.txt file."""
            if self.cookies_box:
                cookies_content = self.cookies_box.get("1.0", "end").strip()
                if cookies_content:
                    os.makedirs(CONFIG_DIR, exist_ok=True)
                    try:
                        with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
                            f.write(cookies_content)
                    except Exception as e:
                        self.log(f"Error saving cookies to {COOKIES_FILE_PATH}: {e}")
                elif os.path.exists(COOKIES_FILE_PATH): # If cookies box is empty, delete the file
                    os.remove(COOKIES_FILE_PATH)

        def get_cookies_text(self):
            if self.cookies_box is None:
                return ""
            return self.cookies_box.get("1.0", "end").strip()

        def open_readme(self):
            self.open_folder(resource_path("README.md"))

        def _set_theme(self, mode):
            ctk.set_appearance_mode(mode.lower())
            self._apply_frosted_glass(self.opacity_var.get())

        def _apply_frosted_glass(self, value):
            intensity = max(0.72, min(1.0, float(value)))
            if os.name == "nt":
                if self._apply_windows_backdrop(intensity):
                    try:
                        self.attributes("-alpha", 1.0)
                    except Exception:
                        pass
                    return

            try:
                self.attributes("-alpha", intensity)
            except Exception:
                pass

        def _apply_windows_backdrop(self, intensity):
            try:
                hwnd = self.winfo_id()
                dark_mode = ctypes.c_int(1 if self.theme_var.get() == "Dark" else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.wintypes.HWND(hwnd),
                    ctypes.c_uint(20),
                    ctypes.byref(dark_mode),
                    ctypes.sizeof(dark_mode),
                )

                backdrop_type = ctypes.c_int(3)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.wintypes.HWND(hwnd),
                    ctypes.c_uint(38),
                    ctypes.byref(backdrop_type),
                    ctypes.sizeof(backdrop_type),
                )
            except Exception:
                pass

            try:
                class AccentPolicy(ctypes.Structure):
                    _fields_ = [
                        ("AccentState", ctypes.c_int),
                        ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_uint),
                        ("AnimationId", ctypes.c_int),
                    ]

                class WindowCompositionAttributeData(ctypes.Structure):
                    _fields_ = [
                        ("Attribute", ctypes.c_int),
                        ("Data", ctypes.c_void_p),
                        ("SizeOfData", ctypes.c_size_t),
                    ]

                tint = "#0B0E14" if self.theme_var.get() == "Dark" else "#F2F2F7"
                alpha = int(130 + (intensity - 0.72) / 0.28 * 90)
                accent = AccentPolicy(
                    4,
                    2,
                    _abgr_from_hex(tint, max(120, min(225, alpha))),
                    0,
                )
                data = WindowCompositionAttributeData(
                    19,
                    ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p),
                    ctypes.sizeof(accent),
                )
                result = ctypes.windll.user32.SetWindowCompositionAttribute(
                    ctypes.wintypes.HWND(self.winfo_id()),
                    ctypes.byref(data),
                )
                return bool(result)
            except Exception:
                return False

        def _on_closing(self):
            # Handles the window closing event, saving cookies before destroying the app.
            self._save_cookies()
            self.destroy()

        def _ui(self, callback, *args):
            self.after(0, lambda: callback(*args))

        def show_restart_dialog(self):
            dialog = ctk.CTkToplevel(self)
            dialog.title("Update yt-dlp")
            width = 420
            height = 190
            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - width) // 2
            y = self.winfo_y() + (self.winfo_height() - height) // 2
            dialog.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            dialog.configure(fg_color=COLORS["surface"])
            self._style_window_chrome(dialog)
            dialog.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                dialog,
                text="yt-dlp was updated",
                font=self._font(22, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, column=0, sticky="w", padx=22, pady=(22, 4))
            ctk.CTkLabel(
                dialog,
                text="Restart the app now to use the updated package.",
                font=self._font(14),
                text_color=COLORS["text_secondary"],
                wraplength=360,
                justify="left",
            ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 18))

            actions = ctk.CTkFrame(dialog, fg_color="transparent")
            actions.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 22))
            actions.grid_columnconfigure((0, 1), weight=1)

            ctk.CTkButton(
                actions,
                text="Restart later",
                command=dialog.destroy,
                corner_radius=12,
                fg_color=COLORS["surface_muted"],
                hover_color=COLORS["accent_soft"],
                text_color=COLORS["text"],
                font=self._font(14, "bold"),
            ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
            self._primary_button(
                actions,
                text="OK",
                command=self.restart_app,
                height=36,
            ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        def restart_app(self):
            self.safe_log("Restarting app...")
            self.update_idletasks()
            os.execl(sys.executable, sys.executable, *sys.argv)

        def log(self, message):
            if self.log_box is None:
                return
            self.log_box.insert("end", str(message) + "\n")
            self.log_box.see("end")

        def clear_activity(self):
            if self.log_box is None:
                return
            self.log_box.delete("1.0", "end")

        def safe_log(self, message):
            self._ui(self.log, message)

        def set_progress(self, percent):
            self.progress.set(max(0, min(100, percent)) / 100)

        def safe_progress(self, percent):
            self._ui(self.set_progress, percent)

        def set_phase(self, phase):
            self.status_label.configure(text=phase)

        def safe_phase(self, phase):
            self._ui(self.set_phase, phase)

        def set_running(self, running):
            self.download_button.configure(state="disabled" if running else "normal")
            self.status_label.configure(text="Downloading" if running else "Ready")

        def change_directory(self):
            new_dir = filedialog.askdirectory()
            if new_dir:
                self.save_path = new_dir
                if self.path_label is not None:
                    self.path_label.configure(text=self.save_path)
                self.log(f"Download folder changed to: {self.save_path}")

        def start_download(self):
            self.open_add_download_dialog()

        def download_handler(self, urls):
            try:
                first_url = next((url.strip() for url in urls if url.strip()), "")
                self.safe_log(f"Detected source: {detect_site(first_url)}")
                download_with_ytdlp(
                    urls=urls,
                    save_dir=self.save_path,
                    format_preset=self.format_var.get(),
                    filename_pattern=self.filename_pattern_var.get().strip() or DEFAULT_FILENAME_PATTERN,
                    download_playlist=self.playlist_var.get(),
                    write_subtitles=self.subtitle_var.get(),
                    write_thumbnail=self.thumbnail_var.get(),
                    cookies_text=self.get_cookies_text(),
                    progress_callback=self.safe_progress,
                    log_callback=self.safe_log,
                    phase_callback=self.safe_phase,
                )
            except Exception as exc:
                self.safe_log(f"Error: {exc}")
            finally:
                self._ui(self.set_running, False)

        def update_ytdlp(self):
            self.tabs.set("Activity")
            thread = threading.Thread(target=self._update_ytdlp_worker, daemon=True)
            thread.start()

        def _update_ytdlp_worker(self):
            self.safe_phase("Updating")
            self.safe_log("Checking yt-dlp update...")
            if getattr(sys, "frozen", False):
                self.safe_log("This one-file build bundles yt-dlp inside the app. Install a newer app build to update bundled yt-dlp.")
                self._ui(
                    messagebox.showinfo,
                    "Update yt-dlp",
                    "This one-file app bundles yt-dlp inside the executable. Download or build a newer app release to update it.",
                )
                self.safe_phase("Ready")
                return

            try:
                command = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
                process = subprocess.run(command, capture_output=True, text=True, check=False)
                output = (process.stdout or "").strip()
                error = (process.stderr or "").strip()
                if output:
                    self.safe_log(output)
                if error:
                    self.safe_log(error)
                if process.returncode == 0:
                    self.safe_log("yt-dlp update complete. Restart the app to use the updated package.")
                    self._ui(self.show_restart_dialog)
                else:
                    self.safe_log(f"yt-dlp update failed with exit code {process.returncode}.")
                    self._ui(messagebox.showerror, "Update yt-dlp", "yt-dlp update failed. Check Activity for details.")
            except Exception as exc:
                self.safe_log(f"yt-dlp update failed: {exc}")
                self._ui(messagebox.showerror, "Update yt-dlp", f"yt-dlp update failed:\n{exc}")
            finally:
                self.safe_phase("Ready")


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
