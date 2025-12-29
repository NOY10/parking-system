from .models import ParkingSession, SessionLocal
from datetime import datetime

class DBManager:
    def __init__(self):
        self.Session = SessionLocal

    def record_arrival(self, slot_id, vehicle_id):
        """Called when a car is first stabilized in a slot."""
        session = self.Session()
        try:
            # Check if an open session already exists for this slot to prevent duplicates
            exists = session.query(ParkingSession).filter(
                ParkingSession.slot_id == slot_id,
                ParkingSession.end_time == None
            ).first()
            
            if not exists:
                new_entry = ParkingSession(
                    slot_id=slot_id, 
                    vehicle_id=int(vehicle_id),
                    start_time=datetime.now()
                )
                session.add(new_entry)
                session.commit()
                print(f"📁 DB: Arrival recorded for Slot {slot_id} (ID: {vehicle_id})")
        except Exception as e:
            print(f"❌ DB Error (Arrival): {e}")
            session.rollback()
        finally:
            session.close()

    # def update_plate(self, vehicle_id, plate_text):
    #     """Called when the ANPR worker finishes processing a batch."""
    #     session = self.Session()
    #     try:
    #         # Match the plate to the session using the unique Tracking ID
    #         record = session.query(ParkingSession).filter(
    #             ParkingSession.vehicle_id == int(vehicle_id)
    #         ).order_by(ParkingSession.start_time.desc()).first()
            
    #         if record:
    #             record.car_plate = plate_text
    #             session.commit()
    #             print(f"📁 DB: Updated Plate for ID {vehicle_id} -> {plate_text}")
    #     except Exception as e:
    #         print(f"❌ DB Error (Plate): {e}")
    #         session.rollback()
    #     finally:
    #         session.close()

    def update_plate(self, vehicle_id, plate_text, image_path=None):
        """Called when the ANPR worker finishes processing a batch."""
        session = self.Session()
        try:
            record = session.query(ParkingSession).filter(
                ParkingSession.vehicle_id == int(vehicle_id)
            ).order_by(ParkingSession.start_time.desc()).first()
            
            if record:
                record.car_plate = plate_text
                if image_path:
                    record.plate_image_path = image_path # <-- SAVE PATH
                session.commit()
                print(f"📁 DB: Updated Plate & Image for ID {vehicle_id}")
        except Exception as e:
            print(f"❌ DB Error (Plate): {e}")
            session.rollback()
        finally:
            session.close()

    def record_departure(self, slot_id, vehicle_id, duration_sec):
        session = self.Session()
        try:
            record = session.query(ParkingSession).filter(
                ParkingSession.slot_id == slot_id,
                ParkingSession.vehicle_id == int(vehicle_id),
                ParkingSession.end_time == None
            ).order_by(ParkingSession.start_time.desc()).first()

            if record:
                record.end_time = datetime.now()
                record.duration_sec = duration_sec
                session.commit()
                print(f"📁 DB: Departure Slot {slot_id}, Vehicle {vehicle_id}")
        except Exception as e:
            print(f"❌ DB Error (Departure): {e}")
            session.rollback()
        finally:
            session.close()
    
    def get_all_sessions(self):
        session = self.Session()
        try:
            records = session.query(ParkingSession).order_by(
                ParkingSession.start_time.desc()
            ).all()
            return records
        finally:
            session.close()


db_manager = DBManager()