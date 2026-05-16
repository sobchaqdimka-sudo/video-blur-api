from flask import Flask, request, send_file, jsonify
import subprocess, requests, uuid, os

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()

    video_url = data.get("video_url")
    ffmpeg_filter = data.get("filter")

    if not video_url or not ffmpeg_filter:
        return jsonify({"error": "video_url and filter are required"}), 400

    job_id = str(uuid.uuid4())
    input_path = f"/tmp/{job_id}_input.mp4"
    output_path = f"/tmp/{job_id}_output.mp4"

    try:
        r = requests.get(video_url, timeout=180)
        r.raise_for_status()

        with open(input_path, "wb") as f:
            f.write(r.content)

        cmd = [
    "ffmpeg", "-y",
    "-i", input_path,
    "-filter_complex", ffmpeg_filter,
    "-map", "[vout]",
    "-map", "0:a?",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "23",
    "-c:a", "aac",
    "-shortest",
    output_path
]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({
                "error": "ffmpeg failed",
                "details": result.stderr
            }), 500

        return send_file(output_path, mimetype="video/mp4", as_attachment=True, download_name="processed.mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
