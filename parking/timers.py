from datetime import datetime

class SlotTimers:
    def __init__(self, slots):
        self.timers = {
            sid: {"start": None, "duration": 0}
            for sid in slots
        }

    def update(self, stable, previous):
        now = datetime.now()

        for sid in self.timers:
            if sid in stable and sid not in previous:
                self.timers[sid]["start"] = now

            if sid not in stable and sid in previous:
                start = self.timers[sid]["start"]
                if start:
                    self.timers[sid]["duration"] += int((now - start).total_seconds())
                    self.timers[sid]["start"] = None

    def build_slot_details(self, stable):
        """Return API-friendly slot status"""
        details = {}

        for sid, timer in self.timers.items():
            details[sid] = {
                "occupied": sid in stable,
                "start_time": timer["start"].isoformat() if timer["start"] else None,
                "duration_sec": timer["duration"]
            }

        return details
