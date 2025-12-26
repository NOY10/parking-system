import threading

lock = threading.Lock()

shared_state = {
    "latest_frame": None,
    "current_status": {
        "total": 0,
        "occupied": 0,
        "free": 0,
        "occupied_slots": [],
        "slots": {}
    },
    "anpr_results": {},
}
