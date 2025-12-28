# from datetime import datetime

# class SlotTimers:
#     def __init__(self, slots):
#         self.timers = {
#             sid: {"start": None, "duration": 0}
#             for sid in slots
#         }

#     def update(self, stable, previous):
#         now = datetime.now()

#         for sid in self.timers:
#             if sid in stable and sid not in previous:
#                 self.timers[sid]["start"] = now

#             if sid not in stable and sid in previous:
#                 start = self.timers[sid]["start"]
#                 if start:
#                     self.timers[sid]["duration"] += int((now - start).total_seconds())
#                     self.timers[sid]["start"] = None

#     def build_slot_details(self, stable):
#         """Return API-friendly slot status"""
#         details = {}

#         for sid, timer in self.timers.items():
#             details[sid] = {
#                 "occupied": sid in stable,
#                 "start_time": timer["start"].isoformat() if timer["start"] else None,
#                 "duration_sec": timer["duration"]
#             }

#         return details

from datetime import datetime


class SlotTimers:
    def __init__(self, slots, db_manager=None):
        """
        slots: iterable of slot IDs
        db_manager: optional DB handler
        """
        self.db = db_manager

        self.timers = {
            sid: {
                "start": None,
                "end": None,
                "duration": 0,
                "vehicle_id": None
            }
            for sid in slots
        }

    def update(self, stable, previous, slot_vehicle_map):
        """
        stable: set of currently occupied slots (after debounce)
        previous: set of previously occupied slots
        slot_vehicle_map: {slot_id: vehicle_track_id}
        """
        now = datetime.now()

        for sid in self.timers:

            # ------------------ ARRIVAL ------------------
            if sid in stable and sid not in previous:
                v_id = slot_vehicle_map.get(sid)

                self.timers[sid]["start"] = now
                self.timers[sid]["end"] = None
                self.timers[sid]["duration"] = 0
                self.timers[sid]["vehicle_id"] = v_id

                if v_id is not None:
                    if self.db:
                        self.db.record_arrival(sid, v_id)
                    print(f"✅ Arrival | Slot {sid} | Vehicle ID {v_id}")
                else:
                    print(f"⚠️ Arrival | Slot {sid} | Vehicle ID NOT FOUND")

            # ------------------ DEPARTURE ------------------
            if sid not in stable and sid in previous:
                start = self.timers[sid]["start"]

                if start:
                    duration = int((now - start).total_seconds())

                    self.timers[sid]["end"] = now
                    self.timers[sid]["duration"] = duration

                    if self.db:
                        self.db.record_departure(
                            sid,
                            self.timers[sid]["vehicle_id"],
                            duration
                        )

                    print(
                        f"🚗 Departure | Slot {sid} | "
                        f"Vehicle {self.timers[sid]['vehicle_id']} | "
                        f"Duration {duration}s"
                    )

                # Reset slot
                self.timers[sid]["start"] = None
                self.timers[sid]["vehicle_id"] = None

    def build_slot_details(self, stable):
        details = {}

        for sid, timer in self.timers.items():
            details[sid] = {
                "occupied": sid in stable,
                "vehicle_id": timer["vehicle_id"],
                "start_time": timer["start"].strftime("%H:%M:%S")
                if timer["start"] else None,
                "end_time": timer["end"].strftime("%H:%M:%S")
                if timer["end"] else None,
                "duration_sec": timer["duration"]
            }

        return details
