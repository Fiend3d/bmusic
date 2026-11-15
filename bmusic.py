import sys
import subprocess
import argparse
import os
import shutil
import time
import importlib


# ─── Dependency checks ────────────────────────────────────────────────────────

def check_ffmpeg():
    """Check if ffmpeg is available, exit with instructions if not."""
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found in PATH.")
        print("  Install: winget install Gyan.FFmpeg")
        print("  Then restart your terminal.")
        sys.exit(1)


def check_js_runtime():
    """Check if a JS runtime (Deno) is available for yt-dlp."""
    if shutil.which("deno"):
        return True
    # Check common install locations on Windows
    common_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\deno\deno.exe"),
        os.path.expandvars(r"%USERPROFILE%\.deno\bin\deno.exe"),
        r"C:\Program Files\Deno\deno.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            # Add to PATH for this session
            os.environ["PATH"] = os.path.dirname(p) + os.pathsep + os.environ["PATH"]
            return True

    print("WARNING: No JS runtime (Deno) found.")
    print("  YouTube extraction may fail or miss formats.")
    print("  Install: winget install DenoLand.Deno")
    print("  Then restart your terminal.")
    print("  Attempting download anyway...\n")
    return False


def update_package(pkg, quiet=True):
    """Upgrade a pip package, but skip if already up to date (fast check)."""
    try:
        importlib.import_module(pkg.replace("-", "_"))
        # Quick version check via pip show
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True, text=True
        )
        # Only upgrade if pip reports it's outdated (skip if recent)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
            capture_output=quiet,
            text=True,
        )
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


# ─── Download logic ───────────────────────────────────────────────────────────

def get_ydl_opts(fallback=False):
    """Build yt-dlp options, with optional fallback format strategy."""
    opts = {
        'format': 'bestaudio/best' if not fallback else 'bestaudio[ext=m4a]/bestaudio/best[ext=m4a]/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }],
        'outtmpl': '%(title)s - %(uploader)s.%(ext)s',
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
        'retries': 10,
        'fragment_retries': 10,
        'socket_timeout': 30,
        'file_access_retries': 3,
        'sleep_interval_requests': 1,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
    }
    if fallback:
        # Try different player clients
        opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        }
    return opts


def download_song(url: str):
    import yt_dlp

    # Strategy 1: normal download
    print("\n[Attempt 1] Standard download...")
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            ydl.download([url])
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"  Failed: {e}")

    # Strategy 2: fallback with alternate player clients
    time.sleep(2)
    print("\n[Attempt 2] Fallback (android client)...")
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(fallback=True)) as ydl:
            ydl.download([url])
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"  Failed: {e}")

    # Strategy 3: download as video (sometimes audio-only formats are blocked)
    time.sleep(2)
    print("\n[Attempt 3] Downloading full video stream...")
    try:
        opts = get_ydl_opts(fallback=True)
        opts['format'] = 'best[ext=mp4]/best'
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"  Failed: {e}")

    return None


def save_link(info, url):
    """Append the download link to links.txt if not already present."""
    if not info:
        return
    title = info.get("title", "Unknown")
    webpage_url = info.get("webpage_url", url)
    line = f"{webpage_url} - {title}\n"
    links_file = os.path.join(os.getcwd(), "links.txt")
    content = ""
    if os.path.exists(links_file):
        with open(links_file, "r", encoding="utf-8") as f:
            content = f.read()
    if line not in content:
        with open(links_file, "a", encoding="utf-8") as f:
            f.write(line)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="My tool for downloading YouTube music")
    parser.add_argument("input", help="YouTube video ID or full URL")
    args = parser.parse_args()

    # Accept both raw ID and full URL
    if args.input.startswith("http"):
        url = args.input
    else:
        url = f"https://www.youtube.com/watch?v={args.input}"
    print(f"URL = {url}")

    # Pre-flight checks
    check_ffmpeg()
    check_js_runtime()
    update_package("yt-dlp")

    # Download with fallback strategies
    info = download_song(url)

    if info:
        save_link(info, url)
        print("\nDone!")
    else:
        print("\nAll attempts failed. Possible causes:")
        print("  - YouTube is blocking your IP (try VPN or wait)")
        print("  - Video is age-restricted or region-locked")
        print("  - Install Deno: winget install DenoLand.Deno")
        sys.exit(1)
