# 07. Xử lý Sự cố Database

## Tổng quan

Tài liệu này mô tả các sự cố thường gặp khi làm việc với SQLite database và cách xử lý chúng một cách hiệu quả.

## 1. Connection Issues

### 1.1 Database Locked Error

**Lỗi:** `database is locked`

**Nguyên nhân:**
- Nhiều process cùng truy cập database
- Connection không được đóng đúng cách
- SQLite không hỗ trợ concurrent writes

**Giải pháp:**
```python
# 1. Thêm timeout cho connection
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Timeout 30 giây
    }
)

# 2. Sử dụng WAL mode
def enable_wal_mode():
    """Bật WAL mode cho concurrent access"""
    from app.database import engine
    
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.commit()

# 3. Đảm bảo đóng connection đúng cách
def safe_database_operation(func):
    """Decorator để đảm bảo đóng connection"""
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close()
    return wrapper
```

### 1.2 Connection Pool Exhausted

**Lỗi:** `QueuePool limit of size X overflow Y reached`

**Nguyên nhân:**
- Quá nhiều connection đồng thời
- Connection không được trả về pool

**Giải pháp:**
```python
# 1. Tăng pool size
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)

# 2. Sử dụng context manager
from contextlib import contextmanager

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. Monitor connection pool
def monitor_connection_pool():
    """Monitor trạng thái connection pool"""
    pool = engine.pool
    print(f"Pool size: {pool.size()}")
    print(f"Checked out: {pool.checkedout()}")
    print(f"Overflow: {pool.overflow()}")
```

### 1.3 Database File Not Found

**Lỗi:** `no such table` hoặc `database file not found`

**Nguyên nhân:**
- Database file chưa được tạo
- Đường dẫn không đúng
- Quyền truy cập file

**Giải pháp:**
```python
# 1. Tạo database và tables
def ensure_database_exists():
    """Đảm bảo database tồn tại"""
    import os
    
    # Tạo thư mục data
    os.makedirs("data", exist_ok=True)
    
    # Khởi tạo database
    from app.database import init_db
    init_db()
    
    print("✅ Database initialized successfully")

# 2. Kiểm tra quyền truy cập
def check_database_permissions():
    """Kiểm tra quyền truy cập database"""
    db_path = "./data/sales_management.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    if not os.access(db_path, os.R_OK | os.W_OK):
        print(f"❌ No read/write permission for: {db_path}")
        return False
    
    print("✅ Database permissions OK")
    return True
```

## 2. Data Integrity Issues

### 2.1 Foreign Key Constraint Violation

**Lỗi:** `FOREIGN KEY constraint failed`

**Nguyên nhân:**
- Tham chiếu đến record không tồn tại
- Xóa record mà vẫn có foreign key references

**Giải pháp:**
```python
# 1. Kiểm tra foreign key trước khi xóa
def safe_delete_product(db: Session, product_id: int):
    """Xóa sản phẩm an toàn"""
    # Kiểm tra có log nào không
    logs_count = db.query(ProductLog).filter(
        ProductLog.product_id == product_id
    ).count()
    
    if logs_count > 0:
        # Xóa logs trước
        db.query(ProductLog).filter(
            ProductLog.product_id == product_id
        ).delete()
    
    # Xóa sản phẩm
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
        return True
    
    return False

# 2. Sử dụng CASCADE DELETE
def setup_cascade_delete():
    """Thiết lập cascade delete"""
    from app.database import engine
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_logs (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """))
        conn.commit()
```

### 2.2 Unique Constraint Violation

**Lỗi:** `UNIQUE constraint failed`

**Nguyên nhân:**
- Thêm record với giá trị unique đã tồn tại
- Update record với giá trị unique đã tồn tại

**Giải pháp:**
```python
# 1. Kiểm tra unique trước khi insert
def safe_create_product(db: Session, product_data: dict):
    """Tạo sản phẩm an toàn"""
    # Kiểm tra SKU unique
    existing = db.query(Product).filter(
        Product.sku == product_data["sku"]
    ).first()
    
    if existing:
        raise ValueError(f"SKU {product_data['sku']} đã tồn tại")
    
    product = Product(**product_data)
    db.add(product)
    db.commit()
    return product

# 2. Upsert (insert or update)
def upsert_product(db: Session, product_data: dict):
    """Insert hoặc update sản phẩm"""
    existing = db.query(Product).filter(
        Product.sku == product_data["sku"]
    ).first()
    
    if existing:
        # Update existing
        for key, value in product_data.items():
            setattr(existing, key, value)
        db.commit()
        return existing
    else:
        # Create new
        product = Product(**product_data)
        db.add(product)
        db.commit()
        return product
```

### 2.3 Data Type Mismatch

**Lỗi:** `datatype mismatch`

**Nguyên nhân:**
- Kiểu dữ liệu không đúng
- String thay vì number
- Date format không đúng

**Giải pháp:**
```python
# 1. Validate data types
def validate_product_data(data: dict):
    """Validate kiểu dữ liệu sản phẩm"""
    errors = []
    
    # Validate price
    try:
        price = float(data.get("price", 0))
        if price < 0:
            errors.append("Price must be positive")
    except (ValueError, TypeError):
        errors.append("Price must be a number")
    
    # Validate quantity
    try:
        quantity = int(data.get("quantity", 0))
        if quantity < 0:
            errors.append("Quantity must be non-negative")
    except (ValueError, TypeError):
        errors.append("Quantity must be an integer")
    
    # Validate SKU
    sku = data.get("sku", "")
    if not isinstance(sku, str) or len(sku) > 100:
        errors.append("SKU must be a string with max 100 characters")
    
    return errors

# 2. Safe type conversion
def safe_convert_types(data: dict):
    """Chuyển đổi kiểu dữ liệu an toàn"""
    converted = {}
    
    for key, value in data.items():
        if key == "price":
            try:
                converted[key] = float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                converted[key] = 0.0
        elif key == "quantity":
            try:
                converted[key] = int(value) if value is not None else 0
            except (ValueError, TypeError):
                converted[key] = 0
        else:
            converted[key] = value
    
    return converted
```

## 3. Performance Issues

### 3.1 Slow Queries

**Triệu chứng:**
- Queries chạy chậm
- Timeout errors
- High CPU usage

**Giải pháp:**
```python
# 1. Monitor query performance
import time
from functools import wraps

def monitor_slow_queries(threshold: float = 1.0):
    """Decorator để monitor slow queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > threshold:
                print(f"⚠️ Slow query: {func.__name__} took {execution_time:.4f}s")
            
            return result
        return wrapper
    return decorator

# 2. Optimize queries
@monitor_slow_queries(threshold=0.5)
def optimized_get_products(db: Session, category: str = None):
    """Query tối ưu"""
    query = db.query(Product.id, Product.name, Product.sku, Product.price)
    
    if category:
        query = query.filter(Product.category == category)
    
    return query.limit(100).all()

# 3. Use indexes
def create_performance_indexes():
    """Tạo indexes cho performance"""
    from app.database import engine
    
    with engine.connect() as conn:
        # Index cho tìm kiếm
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price)"))
        
        # Index cho logs
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_product_id ON product_logs(product_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON product_logs(created_at)"))
        
        conn.commit()
```

### 3.2 Memory Issues

**Triệu chứng:**
- High memory usage
- Out of memory errors
- Slow response times

**Giải pháp:**
```python
# 1. Pagination
def get_products_paginated(db: Session, page: int = 1, per_page: int = 50):
    """Lấy sản phẩm với pagination"""
    offset = (page - 1) * per_page
    return db.query(Product).offset(offset).limit(per_page).all()

# 2. Streaming large datasets
def stream_products(db: Session, batch_size: int = 1000):
    """Stream sản phẩm để tiết kiệm memory"""
    offset = 0
    
    while True:
        products = db.query(Product).offset(offset).limit(batch_size).all()
        
        if not products:
            break
        
        for product in products:
            yield product
        
        offset += batch_size

# 3. Cleanup old data
def cleanup_old_data(db: Session, days: int = 30):
    """Xóa dữ liệu cũ"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Xóa logs cũ
    deleted_logs = db.query(ProductLog).filter(
        ProductLog.created_at < cutoff_date
    ).delete()
    
    db.commit()
    print(f"🗑️ Deleted {deleted_logs} old logs")
```

## 4. Corruption Issues

### 4.1 Database Corruption

**Triệu chứng:**
- `database disk image is malformed`
- Unexpected errors
- Data inconsistency

**Giải pháp:**
```python
# 1. Check database integrity
def check_database_integrity():
    """Kiểm tra tính toàn vẹn database"""
    from app.database import engine
    
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA integrity_check"))
        integrity_result = result.fetchone()[0]
        
        if integrity_result == "ok":
            print("✅ Database integrity check passed")
            return True
        else:
            print(f"❌ Database corruption detected: {integrity_result}")
            return False

# 2. Repair database
def repair_database():
    """Sửa chữa database"""
    from app.database import engine
    
    with engine.connect() as conn:
        # Vacuum database
        conn.execute(text("VACUUM"))
        
        # Rebuild indexes
        conn.execute(text("REINDEX"))
        
        # Analyze database
        conn.execute(text("ANALYZE"))
        
        conn.commit()
    
    print("✅ Database repair completed")

# 3. Restore from backup
def restore_from_backup(backup_path: str):
    """Khôi phục từ backup"""
    import shutil
    
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    
    # Stop application
    # ... stop application code ...
    
    # Restore database
    shutil.copy2(backup_path, "./data/sales_management.db")
    
    print(f"✅ Database restored from: {backup_path}")
```

### 4.2 Data Inconsistency

**Triệu chứng:**
- Duplicate records
- Missing relationships
- Invalid data

**Giải pháp:**
```python
# 1. Find and fix duplicates
def fix_duplicate_skus(db: Session):
    """Tìm và sửa SKU trùng lặp"""
    # Tìm SKU trùng lặp
    duplicates = db.execute(text("""
        SELECT sku, COUNT(*) as count
        FROM products
        GROUP BY sku
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    for sku, count in duplicates:
        print(f"Found {count} duplicates for SKU: {sku}")
        
        # Giữ record mới nhất, xóa các record cũ
        products = db.query(Product).filter(Product.sku == sku).order_by(
            Product.created_at.desc()
        ).all()
        
        # Xóa tất cả trừ record đầu tiên
        for product in products[1:]:
            db.delete(product)
    
    db.commit()
    print(f"Fixed {len(duplicates)} duplicate SKUs")

# 2. Validate relationships
def validate_relationships(db: Session):
    """Kiểm tra tính toàn vẹn relationships"""
    # Tìm logs không có product
    orphaned_logs = db.query(ProductLog).outerjoin(Product).filter(
        Product.id.is_(None)
    ).all()
    
    if orphaned_logs:
        print(f"Found {len(orphaned_logs)} orphaned logs")
        for log in orphaned_logs:
            db.delete(log)
        
        db.commit()
    
    # Tìm products không có logs
    products_without_logs = db.query(Product).outerjoin(ProductLog).filter(
        ProductLog.id.is_(None)
    ).all()
    
    print(f"Found {len(products_without_logs)} products without logs")
```

## 5. Backup và Recovery Issues

### 5.1 Backup Failures

**Lỗi:**
- Backup file corrupted
- Insufficient disk space
- Permission denied

**Giải pháp:**
```python
# 1. Safe backup with verification
def safe_backup():
    """Backup an toàn với verification"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/sales_management_{timestamp}.db"
    
    try:
        # Tạo thư mục backup
        os.makedirs("backups", exist_ok=True)
        
        # Copy database
        shutil.copy2("./data/sales_management.db", backup_path)
        
        # Verify backup
        if verify_backup(backup_path):
            print(f"✅ Backup created successfully: {backup_path}")
            return backup_path
        else:
            os.remove(backup_path)
            raise Exception("Backup verification failed")
            
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

# 2. Check disk space
def check_disk_space():
    """Kiểm tra dung lượng ổ đĩa"""
    import shutil
    
    total, used, free = shutil.disk_usage("./data")
    free_gb = free / (1024**3)
    
    if free_gb < 1.0:  # Ít hơn 1GB
        print(f"⚠️ Low disk space: {free_gb:.2f} GB free")
        return False
    
    return True
```

### 5.2 Recovery Failures

**Lỗi:**
- Backup file not found
- Restore process failed
- Data loss

**Giải pháp:**
```python
# 1. Automated recovery
def automated_recovery():
    """Tự động khôi phục khi có sự cố"""
    # Kiểm tra database integrity
    if not check_database_integrity():
        print("🚨 Database corruption detected!")
        
        # Tìm backup gần nhất
        backup_files = glob.glob("backups/sales_management_*.db")
        if backup_files:
            latest_backup = max(backup_files, key=os.path.getctime)
            print(f"🔄 Attempting recovery from: {latest_backup}")
            
            if restore_from_backup(latest_backup):
                print("✅ Recovery completed successfully")
                return True
        
        print("❌ No valid backup found for recovery")
        return False
    
    return True

# 2. Multiple backup locations
def backup_to_multiple_locations():
    """Backup đến nhiều vị trí"""
    backup_paths = [
        "backups/local/",
        "backups/network/",
        "backups/cloud/"
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"sales_management_{timestamp}.db"
    
    for backup_dir in backup_paths:
        try:
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_name)
            shutil.copy2("./data/sales_management.db", backup_path)
            print(f"✅ Backup to {backup_path}")
        except Exception as e:
            print(f"❌ Backup to {backup_dir} failed: {e}")
```

## 6. Monitoring và Alerting

### 6.1 Database Health Monitoring

```python
class DatabaseMonitor:
    def __init__(self):
        self.alert_thresholds = {
            "file_size_mb": 100,
            "log_count": 10000,
            "slow_query_threshold": 1.0
        }
    
    def check_database_health(self):
        """Kiểm tra sức khỏe database"""
        issues = []
        
        # Kiểm tra file size
        db_size = os.path.getsize("./data/sales_management.db") / (1024 * 1024)
        if db_size > self.alert_thresholds["file_size_mb"]:
            issues.append(f"Database file too large: {db_size:.2f} MB")
        
        # Kiểm tra log count
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            log_count = db.query(ProductLog).count()
            if log_count > self.alert_thresholds["log_count"]:
                issues.append(f"Too many logs: {log_count}")
        finally:
            db.close()
        
        # Kiểm tra integrity
        if not check_database_integrity():
            issues.append("Database integrity check failed")
        
        return issues
    
    def send_alert(self, issues: list):
        """Gửi cảnh báo"""
        if issues:
            message = "Database Health Alert:\n" + "\n".join(issues)
            print(f"🚨 {message}")
            # Gửi email, Slack, etc.
```

### 6.2 Performance Monitoring

```python
def monitor_database_performance():
    """Monitor performance database"""
    from app.database import engine
    
    with engine.connect() as conn:
        # Kiểm tra cache hit ratio
        result = conn.execute(text("PRAGMA cache_stats"))
        cache_stats = result.fetchone()
        
        # Kiểm tra page count
        result = conn.execute(text("PRAGMA page_count"))
        page_count = result.fetchone()[0]
        
        # Kiểm tra fragmentation
        result = conn.execute(text("PRAGMA page_count"))
        total_pages = result.fetchone()[0]
        
        result = conn.execute(text("PRAGMA freelist_count"))
        free_pages = result.fetchone()[0]
        
        fragmentation = (free_pages / total_pages) * 100 if total_pages > 0 else 0
        
        print(f"Database Performance:")
        print(f"  - Cache hits: {cache_stats[0]}")
        print(f"  - Total pages: {total_pages}")
        print(f"  - Fragmentation: {fragmentation:.2f}%")
        
        if fragmentation > 20:
            print("⚠️ High fragmentation detected - consider VACUUM")
``` 