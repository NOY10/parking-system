from anpr.worker import task_queue
from config.settings import BUFFER_SIZE

car_buffer = {}
processed = set()

def update_anpr(v_id, frame_crop):
    if v_id in processed:
        return

    car_buffer.setdefault(v_id, []).append(frame_crop)

    if len(car_buffer[v_id]) >= BUFFER_SIZE:
        if not task_queue.full():
            task_queue.put((v_id, car_buffer[v_id]))
            processed.add(v_id)
        car_buffer.pop(v_id, None)
