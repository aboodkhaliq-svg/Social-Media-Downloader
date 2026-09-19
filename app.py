from flask import Flask, render_template, request, send_file
import yt_dlp
import imageio_ffmpeg
import tempfile
import shutil
from pathlib import Path

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    format_type = request.form.get("format", "mp4")

    if not url:
        return "Please enter a URL.", 400

    folder = Path(tempfile.mkdtemp())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    try:
        if format_type == "mp3":

            options = {
                "format": "bestaudio/best",
                "outtmpl": str(folder / "%(title)s.%(ext)s"),
                "noplaylist": True,
                "quiet": False,
                "ffmpeg_location": ffmpeg,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192"
                    }
                ]
            }

        elif format_type == "mp4":

            options = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": str(folder / "%(title)s.%(ext)s"),
                "noplaylist": True,
                "quiet": False,
                "ffmpeg_location": ffmpeg,
                "merge_output_format": "mp4"
            }

        else:
            return "Invalid format.", 400

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "download")

        files = list(folder.iterdir())

        if not files:
            return "The download failed because no file was created.", 500

        if format_type == "mp3":
            media = next(
                (file for file in files if file.suffix.lower() == ".mp3"),
                None
            )
        else:
            media = next(
                (
                    file for file in files
                    if file.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov"]
                ),
                None
            )

        if media is None:
            return "The requested MP4 file could not be created.", 500

        extension = "mp3" if format_type == "mp3" else "mp4"

        filename = f"{title}.{extension}"

        response = send_file(
            media,
            as_attachment=True,
            download_name=filename
        )

        @response.call_on_close
        def cleanup():
            shutil.rmtree(folder, ignore_errors=True)

        return response

    except Exception as error:
        shutil.rmtree(folder, ignore_errors=True)
        return f"Download error: {error}", 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )