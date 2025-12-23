from flask import Flask, Response, jsonify, render_template
from flask_cors import CORS
import cv2, time

from services.video_processor import start_video_thread
from state.shared_state import shared_state, lock

app = Flask(__name__)
CORS(app)

start_video_thread()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    def generate():
        while True:
            with lock:
                frame = shared_state["latest_frame"]
            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" +
                    buffer.tobytes() + b"\r\n"
                )
            time.sleep(0.03)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/parking_status")
def parking_status():
    with lock:
        return jsonify(shared_state["current_status"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
