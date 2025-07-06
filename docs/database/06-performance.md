# 06. Tối ưu Hiệu suất Database

## Tổng quan

Tối ưu hiệu suất database là yếu tố quan trọng để đảm bảo ứng dụng hoạt động nhanh và ổn định. Tài liệu này mô tả các kỹ thuật tối ưu cho SQLite database.

## 1. Indexing Strategy

### 1.1 Primary Indexes

```sql
-- Index cho tìm kiếm theo SKU (unique)
CREATE INDEX idx_products_sku ON products(sku);

-- Index cho tìm kiếm theo tên
CREATE INDEX idx_products_name ON products(name);

-- Index cho filter theo danh mục
CREATE INDEX idx_products_category ON products(category);

-- Index cho sắp xếp theo thời gian
CREATE INDEX idx_products_created_at ON products(created_at);
CREATE INDEX idx_products_updated_at ON products(updated_at);
```

### 1.2 Composite Indexes

```sql
-- Index cho tìm kiếm theo danh mục và giá
CREATE INDEX idx_products_category_price ON products(category, price);

-- Index cho tìm kiếm theo danh mục và số lượng
CREATE INDEX idx_products_category_quantity ON products(category, quantity);

-- Index cho log queries
CREATE INDEX idx_logs_product_action ON product_logs(product_id, action);
CREATE INDEX idx_logs_created_at ON product_logs(created_at);
```

### 1.3 Partial Indexes

```sql
-- Index chỉ cho sản phẩm có số lượng > 0
CREATE INDEX idx_products_in_stock ON products(id) WHERE quantity > 0;

-- Index chỉ cho log của 30 ngày gần nhất
CREATE INDEX idx_logs_recent ON product_logs(created_at) 
WHERE created_at >= datetime('now', '-30 days');
```

## 2. Query Optimization

### 2.1 Select Specific Columns

```python
# ❌ Không tốt - Select tất cả columns
products = db.query(Product).all()

# ✅ Tốt - Chỉ select cần thiết
products = db.query(Product.id, Product.name, Product.sku).all()

# ✅ Tốt hơn - Sử dụng select()
from sqlalchemy import select
stmt = select(Product.id, Product.name, Product.sku)
products = db.execute(stmt).fetchall()
```

### 2.2 Use LIMIT and OFFSET

```python
# Pagination hiệu quả
def get_products_paginated(db: Session, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    return db.query(Product).offset(offset).limit(per_page).all()

# Lấy top products theo giá
def get_expensive_products(db: Session, limit: int = 10):
    return db.query(Product).order_by(Product.price.desc()).limit(limit).all()
```

### 2.3 Avoid N+1 Queries

```python
# ❌ Không tốt - N+1 queries
products = db.query(Product).all()
for product in products:
    logs = product.logs  # Query riêng cho mỗi product

# ✅ Tốt - Eager loading
from sqlalchemy.orm import joinedload
products = db.query(Product).options(
    joinedload(Product.logs)
).all()

# ✅ Tốt hơn - Selectinload cho large datasets
from sqlalchemy.orm import selectinload
products = db.query(Product).options(
    selectinload(Product.logs)
).all()
```

### 2.4 Use EXISTS instead of COUNT

```python
# ❌ Không tốt - COUNT query
has_products = db.query(Product).count() > 0

# ✅ Tốt - EXISTS query
from sqlalchemy import exists
has_products = db.query(exists().where(Product.id > 0)).scalar()
```

## 3. Connection Pool Optimization

### 3.1 SQLite Connection Pool

```python
from sqlalchemy.pool import StaticPool

# Cấu hình connection pool cho SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Static pool cho SQLite
    pool_size=1,           # Chỉ 1 connection
    max_overflow=0,        # Không overflow
    pool_timeout=30,       # Timeout 30 giây
    pool_recycle=3600,     # Recycle sau 1 giờ
)
```

### 3.2 Session Management

```python
# Context manager cho session
from contextlib import contextmanager

@contextmanager
def get_db_session():
    """Context manager cho database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Sử dụng
def create_product_safe(product_data: dict):
    with get_db_session() as db:
        product = Product(**product_data)
        db.add(product)
        db.flush()  # Lấy ID mà không commit
        return product
```

## 4. Caching Strategies

### 4.1 Application Level Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 phút
    
    def get(self, key: str):
        """Lấy giá trị từ cache"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_timeout):
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value):
        """Lưu giá trị vào cache"""
        self.cache[key] = (value, datetime.now())
    
    def clear(self):
        """Xóa cache"""
        self.cache.clear()

# Global cache instance
cache_manager = CacheManager()

# Cached functions
@lru_cache(maxsize=128)
def get_categories_cached(db: Session):
    """Cache danh sách danh mục"""
    return db.query(Product.category).distinct().all()

def get_product_by_id_cached(db: Session, product_id: int):
    """Cache product theo ID"""
    cache_key = f"product_{product_id}"
    cached_product = cache_manager.get(cache_key)
    
    if cached_product:
        return cached_product
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        cache_manager.set(cache_key, product)
    
    return product
```

### 4.2 Database Query Caching

```python
def cached_query(query_func, cache_key: str, timeout: int = 300):
    """Decorator cho cached queries"""
    def decorator(*args, **kwargs):
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        result = query_func(*args, **kwargs)
        cache_manager.set(cache_key, result)
        return result
    return decorator

# Sử dụng
@cached_query("expensive_products", timeout=600)
def get_expensive_products(db: Session):
    return db.query(Product).filter(Product.price > 1000000).all()
```

## 5. Bulk Operations

### 5.1 Bulk Insert

```python
def bulk_insert_products(db: Session, products_data: list):
    """Bulk insert nhiều sản phẩm"""
    products = [Product(**data) for data in products_data]
    
    # Sử dụng bulk_save_objects cho hiệu suất tốt
    db.bulk_save_objects(products)
    db.commit()
    
    return len(products)

# Sử dụng batch processing cho large datasets
def bulk_insert_large_dataset(db: Session, products_data: list, batch_size: int = 1000):
    """Bulk insert với batch processing"""
    total_inserted = 0
    
    for i in range(0, len(products_data), batch_size):
        batch = products_data[i:i + batch_size]
        products = [Product(**data) for data in batch]
        
        db.bulk_save_objects(products)
        db.commit()
        
        total_inserted += len(products)
        print(f"Inserted batch {i//batch_size + 1}: {len(products)} products")
    
    return total_inserted
```

### 5.2 Bulk Update

```python
def bulk_update_prices(db: Session, category: str, price_increase: float):
    """Bulk update giá sản phẩm"""
    updated_count = db.query(Product).filter(
        Product.category == category
    ).update({
        Product.price: Product.price + price_increase
    })
    
    db.commit()
    return updated_count

def bulk_update_quantities(db: Session, updates: dict):
    """Bulk update số lượng theo ID"""
    for product_id, new_quantity in updates.items():
        db.query(Product).filter(
            Product.id == product_id
        ).update({
            Product.quantity: new_quantity
        })
    
    db.commit()
    return len(updates)
```

## 6. Database Maintenance

### 6.1 Regular Maintenance

```python
def perform_database_maintenance():
    """Thực hiện bảo trì database định kỳ"""
    from app.database import engine
    
    with engine.connect() as conn:
        # Vacuum database
        conn.execute(text("VACUUM"))
        
        # Analyze database
        conn.execute(text("ANALYZE"))
        
        # Update statistics
        conn.execute(text("ANALYZE sqlite_master"))
        
        conn.commit()
    
    print("✅ Database maintenance completed")

# Lập lịch maintenance
def schedule_maintenance():
    """Lập lịch maintenance hàng tuần"""
    import schedule
    
    schedule.every().sunday.at("03:00").do(perform_database_maintenance)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check mỗi giờ
```

### 6.2 Log Cleanup

```python
def cleanup_old_logs(db: Session, days: int = 30):
    """Xóa log cũ để tối ưu performance"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    deleted_count = db.query(ProductLog).filter(
        ProductLog.created_at < cutoff_date
    ).delete()
    
    db.commit()
    print(f"🗑️ Deleted {deleted_count} old logs")
    return deleted_count
```

## 7. Monitoring và Profiling

### 7.1 Query Performance Monitoring

```python
import time
from functools import wraps

def monitor_query_performance(func):
    """Decorator để monitor query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 1.0:  # Log queries chậm
            print(f"⚠️ Slow query detected: {func.__name__} took {execution_time:.4f}s")
        
        return result
    return wrapper

# Sử dụng
@monitor_query_performance
def get_products_with_logs(db: Session):
    return db.query(Product).options(joinedload(Product.logs)).all()
```

### 7.2 Database Statistics

```python
def get_database_statistics():
    """Lấy thống kê database"""
    from app.database import engine
    
    with engine.connect() as conn:
        # Table sizes
        result = conn.execute(text("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """))
        tables = result.fetchall()
        
        stats = {}
        for table_name, _ in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.fetchone()[0]
            stats[table_name] = count
        
        # Database size
        result = conn.execute(text("PRAGMA page_count"))
        page_count = result.fetchone()[0]
        
        result = conn.execute(text("PRAGMA page_size"))
        page_size = result.fetchone()[0]
        
        db_size = page_count * page_size
        
        return {
            "table_counts": stats,
            "database_size_bytes": db_size,
            "database_size_mb": db_size / (1024 * 1024)
        }
```

## 8. Configuration Optimization

### 8.1 SQLite Configuration

```python
def optimize_sqlite_config():
    """Tối ưu cấu hình SQLite"""
    from app.database import engine
    
    with engine.connect() as conn:
        # Enable WAL mode cho concurrent access
        conn.execute(text("PRAGMA journal_mode=WAL"))
        
        # Tăng cache size
        conn.execute(text("PRAGMA cache_size=10000"))
        
        # Tăng temp store
        conn.execute(text("PRAGMA temp_store=MEMORY"))
        
        # Optimize synchronous
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        
        # Optimize mmap size
        conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
        
        conn.commit()
    
    print("✅ SQLite configuration optimized")
```

### 8.2 Environment-based Configuration

```python
import os

def get_optimized_engine():
    """Tạo engine với cấu hình tối ưu theo environment"""
    is_production = os.getenv("ENVIRONMENT") == "production"
    
    if is_production:
        # Production settings
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            pool_size=1,
            max_overflow=0,
            pool_timeout=30,
            echo=False,  # Disable SQL logging
        )
    else:
        # Development settings
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=True,  # Enable SQL logging
        )
    
    return engine
```

## 9. Performance Testing

### 9.1 Load Testing

```python
import concurrent.futures
import time

def load_test_database(num_requests: int = 1000, num_threads: int = 10):
    """Load test database performance"""
    from app.database import SessionLocal
    
    def make_request():
        db = SessionLocal()
        try:
            # Simulate typical query
            products = db.query(Product).limit(10).all()
            return len(products)
        finally:
            db.close()
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Load test results:")
    print(f"  - Requests: {num_requests}")
    print(f"  - Threads: {num_threads}")
    print(f"  - Total time: {total_time:.2f}s")
    print(f"  - Requests per second: {num_requests/total_time:.2f}")
    
    return {
        "total_requests": num_requests,
        "total_time": total_time,
        "requests_per_second": num_requests/total_time
    }
```

### 9.2 Query Performance Testing

```python
def benchmark_queries():
    """Benchmark các loại query khác nhau"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    queries = [
        ("Simple select", lambda: db.query(Product).limit(100).all()),
        ("Filter by category", lambda: db.query(Product).filter(Product.category == "Laptop").all()),
        ("Search by name", lambda: db.query(Product).filter(Product.name.ilike("%laptop%")).all()),
        ("Order by price", lambda: db.query(Product).order_by(Product.price.desc()).limit(50).all()),
        ("Join with logs", lambda: db.query(Product).options(joinedload(Product.logs)).limit(20).all()),
    ]
    
    results = {}
    
    for name, query_func in queries:
        start_time = time.time()
        result = query_func()
        end_time = time.time()
        
        execution_time = end_time - start_time
        results[name] = {
            "execution_time": execution_time,
            "result_count": len(result)
        }
        
        print(f"{name}: {execution_time:.4f}s ({len(result)} results)")
    
    return results
``` 