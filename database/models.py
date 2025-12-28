# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sqlalchemy

Base = declarative_base()

class ParkingSession(Base):
    __tablename__ = 'parking_sessions'
    
    id = Column(Integer, primary_key=True)
    slot_id = Column(Integer, nullable=False)
    car_plate = Column(String(20), default="DETECTING...")
    vehicle_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, nullable=True)
# Connection string
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/parking_db"
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        # 1. Test the connection
        with engine.connect() as conn:
            print("📡 [DB INFO] Connection to PostgreSQL successful.")
            
        # 2. Create tables
        print("🛠️ [DB INFO] Syncing tables with metadata...")
        Base.metadata.create_all(bind=engine)
        
        # 3. Double check if table exists
        inspector = sqlalchemy.inspect(engine)
        if 'parking_sessions' in inspector.get_table_names():
            print("🚀 [DB SUCCESS] Table 'parking_sessions' verified in 'parking_db'.")
        else:
            print("⚠️ [DB WARNING] Table creation finished but table not found. Check your schema/permissions.")

    except Exception as e:
        print(f"❌ [DB ERROR] Could not initialize database: {e}")