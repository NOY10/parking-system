class Debouncer:
    def __init__(self, slots, min_frames):
        self.counts = {sid: {"occ": 0, "free": 0} for sid in slots}
        self.stable = set()
        self.min_frames = min_frames

    def update(self, occupied):
        for sid in self.counts:
            if sid in occupied:
                self.counts[sid]["occ"] += 1
                self.counts[sid]["free"] = 0
                if self.counts[sid]["occ"] >= self.min_frames:
                    self.stable.add(sid)
            else:
                self.counts[sid]["free"] += 1
                self.counts[sid]["occ"] = 0
                if self.counts[sid]["free"] >= self.min_frames:
                    self.stable.discard(sid)
        return self.stable
