from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Tạo thư mục data nếu chưa có
os.makedirs("data", exist_ok=True)

# Kết nối SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/sales_management.db"

# Tạo engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Cần thiết cho SQLite
)

# Tạo SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho models
Base = declarative_base()

def get_db():
    """Dependency để lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Khởi tạo database và tạo các bảng"""
    from app.models import Base
    Base.metadata.create_all(bind=engine) 