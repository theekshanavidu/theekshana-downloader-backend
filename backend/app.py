from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import tempfile, os

app = Flask(__name__)
CORS(app)

@app.route("/api/info")
def info():
    url = request.args.get("url")
    if not url:
        return jsonify({"error":"Missing URL"}), 400
    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        fmts=[]
        for f in info["formats"]:
            if f.get("height"):
                size = f.get("filesize") or f.get("filesize_approx") or 0
                fmts.append({
                    "format_id": f["format_id"],
                    "label": f"{f.get('height')}p ({f.get('ext')}, {round(size/1024/1024,1)} MB)"
                })
        return jsonify({
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "formats": fmts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data["url"]
    mode = data.get("mode", "video")
    fmt = data.get("format_id")
    temp = tempfile.mkdtemp()
    ydl_opts = {
        "outtmpl": os.path.join(temp, "%(title)s.%(ext)s"),
        "quiet": True
    }
    if mode == "audio":
        ydl_opts.update({
            "format": "bestaudio",
            "postprocessors": [{"key": "FFmpegExtractAudio","preferredcodec": "mp3"}]
        })
    else:
        ydl_opts["format"] = f"{fmt}+bestaudio/best" if fmt else "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    file_path = ydl.prepare_filename(info)
    if mode == "audio":
        file_path = os.path.splitext(file_path)[0] + ".mp3"
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
