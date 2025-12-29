# from flask import Flask, Response, jsonify, render_template
# from flask_cors import CORS
# import cv2, time

# from services.video_processor import start_video_thread
# from state.shared_state import shared_state, lock

# app = Flask(__name__)
# CORS(app)

# start_video_thread()

# @app.route("/")
# def index():
#     return render_template("index.html")

# @app.route("/video_feed")
# def video_feed():
#     def generate():
#         while True:
#             with lock:
#                 frame = shared_state["latest_frame"]
#             if frame is not None:
#                 _, buffer = cv2.imencode(".jpg", frame)
#                 yield (
#                     b"--frame\r\n"
#                     b"Content-Type: image/jpeg\r\n\r\n" +
#                     buffer.tobytes() + b"\r\n"
#                 )
#             time.sleep(0.03)

#     return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# @app.route("/parking_status")
# def parking_status():
#     with lock:
#         return jsonify(shared_state["current_status"])

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)




from flask import Flask, Response, jsonify, render_template
from flask_cors import CORS
import cv2, time

from services.video_processor import start_video_thread
from state.shared_state import shared_state, lock
from database.models import init_db  

from database.manager import db_manager
from database.models import ParkingSession


app = Flask(__name__)
CORS(app)

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

@app.route("/parking_sessions", methods=["GET"])
def get_parking_sessions():
    """Fetches all parking history from the database."""
    try:
        records = db_manager.get_all_sessions()
        
        data = []
        for r in records:
            data.append({
                "id": r.id,
                "slot_id": r.slot_id,
                "car_plate": r.car_plate,
                "vehicle_id": r.vehicle_id,
                "start_time": r.start_time.strftime("%Y-%m-%d %H:%M:%S") if r.start_time else None,
                "end_time": r.end_time.strftime("%Y-%m-%d %H:%M:%S") if r.end_time else None,
                "duration_sec": r.duration_sec
            })
            
        return jsonify(data)
    except Exception as e:
        print(f"❌ Error fetching sessions: {e}")
        return jsonify({"error": "Could not retrieve sessions"}), 500


if __name__ == "__main__":
    init_db() 
    start_video_thread()
    print("🚀 Flask server starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)