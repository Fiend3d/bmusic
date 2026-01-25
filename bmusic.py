import sys
import subprocess
import argparse
import os


def update_package(pkg):
    subprocess.check_call([
        sys.executable,
        "-m", "pip",
        "install",
        "--upgrade",
        pkg,
    ])


def download_song(url: str):
    import yt_dlp

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }],
        'outtmpl': '%(title)s - %(uploader)s.%(ext)s',
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info = ydl.extract_info(url, download=False)

            title = info.get("title")
            webpage_url = info.get("webpage_url", url)
            line = f"{webpage_url} - {title}\n"
            cwd = os.getcwd()
            links = f"{cwd}\\links.txt"
            content = ""
            if os.path.exists(links):
                with open(links, "r") as f:
                    content = f.read()
            if line not in content:
                with open(links, "a") as f:
                    f.write(line)

        print("Done!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="My tool for downloading YouTube music")
    parser.add_argument("input", help="Input URL")
    args = parser.parse_args()
    url = f"https://www.youtube.com/watch?v={args.input}"
    print(f"URL = {url}")

    update_package("yt-dlp")
    download_song(url)
