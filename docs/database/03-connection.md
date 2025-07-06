# 03. Cấu hình Kết nối Database

## Tổng quan

Hệ thống sử dụng **SQLAlchemy** để quản lý kết nối database với **SQLite** làm database engine. Cấu hình được thiết kế để đơn giản, hiệu quả và dễ bảo trì.

## 1. Database Configuration

### 1.1 File cấu hình: `app/database.py`

```python
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
```

### 1.2 Chi tiết từng thành phần

#### Database URL
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/sales_management.db"
```

**Cú pháp SQLite URL:**
- `sqlite:///` - Protocol cho SQLite
- `./data/` - Thư mục chứa file database
- `sales_management.db` - Tên file database

**Các dạng URL khác:**
```python
# Database trong thư mục hiện tại
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

# Database trong thư mục cụ thể
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/myapp.db"

# Database trong memory (cho testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Database với đường dẫn tuyệt đối
SQLALCHEMY_DATABASE_URL = "sqlite:////absolute/path/to/database.db"
```

#### Engine Configuration
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
```

**Connect Args cho SQLite:**
- `check_same_thread=False` - Cho phép truy cập từ nhiều thread
- Cần thiết cho FastAPI (async framework)

**Các options khác:**
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,  # Log SQL queries (debug mode)
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max overflow connections
    pool_timeout=30,  # Timeout for getting connection
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

#### Session Configuration
```python
SessionLocal = sessionmaker(
    autocommit=False,  # Không tự động commit
    autoflush=False,   # Không tự động flush
    bind=engine        # Bind với engine
)
```

**Các options:**
- `autocommit=False` - Phải commit thủ công
- `autoflush=False` - Không tự động flush changes
- `bind=engine` - Liên kết với engine

## 2. Dependency Injection

### 2.1 Database Session Dependency

```python
def get_db():
    """Dependency để lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Cách hoạt động:**
1. Tạo session mới khi request bắt đầu
2. Yield session cho route handler
3. Đóng session khi request kết thúc
4. Đảm bảo session luôn được đóng

### 2.2 Sử dụng trong FastAPI Routes

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

@router.get("/products")
async def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products
```

**Lợi ích:**
- ✅ Tự động quản lý session lifecycle
- ✅ Thread-safe
- ✅ Không memory leak
- ✅ Dễ test với dependency injection

## 3. Database Initialization

### 3.1 Khởi tạo Database

```python
def init_db():
    """Khởi tạo database và tạo các bảng"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
```

**Cách hoạt động:**
1. Import tất cả models (để đăng ký với Base)
2. Tạo tất cả bảng dựa trên model definitions
3. Tạo indexes và constraints

### 3.2 Script khởi tạo: `init_db.py`

```python
#!/usr/bin/env python3
"""
Script khởi tạo database và thêm dữ liệu mẫu
"""

import os
import sys
from datetime import datetime

# Thêm thư mục gốc vào path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models import Product, ProductLog

def main():
    """Hàm chính"""
    print("🚀 Khởi tạo hệ thống Quản lý Bán hàng...")
    
    # Khởi tạo database
    print("📊 Đang khởi tạo database...")
    init_db()
    print("✅ Database đã được khởi tạo thành công!")
    
    # Tạo dữ liệu mẫu
    create_sample_data()
    
    print("\n🎯 Hệ thống đã sẵn sàng!")

if __name__ == "__main__":
    main()
```

## 4. Connection Pool Management

### 4.1 SQLite Connection Pool

SQLite không có connection pool thực sự, nhưng SQLAlchemy vẫn quản lý connections:

```python
# Cấu hình connection pool
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Static pool cho SQLite
    pool_size=1,           # Chỉ 1 connection cho SQLite
    max_overflow=0,        # Không overflow
    pool_timeout=30,       # Timeout 30 giây
)
```

### 4.2 Connection Lifecycle

```
Request Start
    ↓
Create Session
    ↓
Execute Queries
    ↓
Commit/Rollback
    ↓
Close Session
    ↓
Request End
```

## 5. Error Handling

### 5.1 Database Connection Errors

```python
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

def safe_db_operation(func):
    """Decorator để xử lý lỗi database"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            # Log error
            print(f"Database error: {e}")
            # Rollback session
            db.rollback()
            # Raise HTTP exception
            raise HTTPException(status_code=500, detail="Database error")
    return wrapper
```

### 5.2 Sử dụng trong Routes

```python
@router.post("/products")
@safe_db_operation
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
```

## 6. Configuration Management

### 6.1 Environment Variables

```python
import os
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sales_management.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "1"))
DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))

# Tạo engine với config từ environment
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=DATABASE_ECHO,
    pool_size=DATABASE_POOL_SIZE,
    pool_timeout=DATABASE_POOL_TIMEOUT,
)
```

### 6.2 Configuration Classes

```python
from pydantic import BaseSettings

class DatabaseSettings(BaseSettings):
    url: str = "sqlite:///./data/sales_management.db"
    echo: bool = False
    pool_size: int = 1
    pool_timeout: int = 30
    
    class Config:
        env_prefix = "DATABASE_"

# Sử dụng
db_settings = DatabaseSettings()
engine = create_engine(
    db_settings.url,
    connect_args={"check_same_thread": False},
    echo=db_settings.echo,
    pool_size=db_settings.pool_size,
    pool_timeout=db_settings.pool_timeout,
)
```

## 7. Testing Configuration

### 7.1 Test Database

```python
# test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

@pytest.fixture
def test_db():
    """Tạo test database"""
    # Tạo in-memory database cho testing
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Tạo tables
    Base.metadata.create_all(bind=engine)
    
    # Yield session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
```

### 7.2 Sử dụng trong Tests

```python
def test_create_product(test_db):
    """Test tạo sản phẩm"""
    product = Product(
        name="Test Product",
        sku="TEST-001",
        price=1000.0
    )
    test_db.add(product)
    test_db.commit()
    
    assert product.id is not None
    assert product.name == "Test Product"
```

## 8. Monitoring và Logging

### 8.1 Database Logging

```python
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log database operations
def log_db_operation(operation: str, table: str, record_id: int = None):
    """Log database operations"""
    logger.info(f"Database {operation} on {table}" + (f" ID: {record_id}" if record_id else ""))

# Sử dụng
@router.post("/products")
async def create_product(product_data: dict, db: Session = Depends(get_db)):
    product = Product(**product_data)
    db.add(product)
    db.commit()
    log_db_operation("CREATE", "products", product.id)
    return product
```

### 8.2 Performance Monitoring

```python
import time
from functools import wraps

def monitor_db_performance(func):
    """Decorator để monitor performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"Database operation took {execution_time:.4f} seconds")
        
        return result
    return wrapper
```

## 9. Backup và Recovery

### 9.1 Database Backup

```python
import shutil
from datetime import datetime

def backup_database():
    """Backup database file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/sales_management_{timestamp}.db"
    
    # Tạo thư mục backup nếu chưa có
    os.makedirs("backups", exist_ok=True)
    
    # Copy database file
    shutil.copy2("data/sales_management.db", backup_path)
    
    logger.info(f"Database backed up to {backup_path}")
    return backup_path
```

### 9.2 Database Recovery

```python
def restore_database(backup_path: str):
    """Restore database từ backup"""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Stop application (nếu cần)
    # ...
    
    # Restore database
    shutil.copy2(backup_path, "data/sales_management.db")
    
    logger.info(f"Database restored from {backup_path}")
```

## 10. Troubleshooting

### 10.1 Common Issues

**1. Database locked error:**
```python
# Giải pháp: Thêm timeout
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)
```

**2. Connection pool exhausted:**
```python
# Giải pháp: Tăng pool size hoặc giảm concurrent requests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

**3. Database file not found:**
```python
# Giải pháp: Tạo thư mục và file
os.makedirs("data", exist_ok=True)
init_db()  # Tạo tables nếu chưa có
```

### 10.2 Debug Mode

```python
# Bật debug mode để xem SQL queries
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True  # Log tất cả SQL queries
)
``` 