# 01. Tổng quan Kiến trúc Database

## Kiến trúc tổng thể

Hệ thống sử dụng kiến trúc **3-layer** với database layer được thiết kế theo mô hình **Repository Pattern**:

```
┌─────────────────┐
│   Presentation  │ ← FastAPI Routes
├─────────────────┤
│   Business      │ ← Service Layer (có thể mở rộng)
├─────────────────┤
│   Data Access   │ ← SQLAlchemy ORM
├─────────────────┤
│   Database      │ ← SQLite File
└─────────────────┘
```

## Database Engine: SQLite

### Tại sao chọn SQLite?

**Ưu điểm:**
- ✅ **Zero-configuration**: Không cần cài đặt server riêng
- ✅ **File-based**: Database là một file duy nhất
- ✅ **ACID compliance**: Đảm bảo tính toàn vẹn dữ liệu
- ✅ **Lightweight**: Nhẹ, nhanh cho ứng dụng nhỏ và vừa
- ✅ **Built-in Python**: Có sẵn trong Python standard library
- ✅ **Cross-platform**: Chạy trên mọi hệ điều hành

**Nhược điểm:**
- ❌ **Concurrent access**: Hạn chế truy cập đồng thời
- ❌ **Scalability**: Không phù hợp cho ứng dụng lớn
- ❌ **Network access**: Không thể truy cập từ xa trực tiếp

### Khi nào sử dụng SQLite?

✅ **Phù hợp cho:**
- Ứng dụng desktop
- Ứng dụng web nhỏ (1-10 users)
- Prototype/MVP
- Development/Testing
- Embedded systems

❌ **Không phù hợp cho:**
- Ứng dụng web lớn (>100 concurrent users)
- Distributed systems
- High-availability requirements
- Complex transactions

## ORM: SQLAlchemy

### Tại sao chọn SQLAlchemy?

**Ưu điểm:**
- ✅ **Type safety**: Kiểm tra kiểu dữ liệu tại compile time
- ✅ **Database agnostic**: Dễ dàng chuyển đổi database
- ✅ **Migration support**: Alembic cho schema changes
- ✅ **Query builder**: API mạnh mẽ cho queries
- ✅ **Relationship management**: Xử lý quan hệ tự động
- ✅ **Connection pooling**: Quản lý connection hiệu quả

### Core Components

```python
# 1. Engine - Kết nối database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. Session - Quản lý transaction
SessionLocal = sessionmaker(bind=engine)

# 3. Base - Base class cho models
Base = declarative_base()

# 4. Models - Định nghĩa schema
class Product(Base):
    __tablename__ = "products"
    # ... fields
```

## Schema Design

### Nguyên tắc thiết kế

1. **Normalization**: Tuân thủ 3NF (Third Normal Form)
2. **Audit Trail**: Ghi lại mọi thay đổi
3. **Soft Delete**: Không xóa dữ liệu thật
4. **Timestamps**: Tự động cập nhật thời gian
5. **Indexing**: Tối ưu cho queries thường dùng

### Database Schema

```sql
-- Bảng sản phẩm
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    price FLOAT NOT NULL,
    quantity INTEGER DEFAULT 0,
    category VARCHAR(100),
    description TEXT,
    images JSON DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bảng log thay đổi
CREATE TABLE product_logs (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100) DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

## Data Flow

### 1. Create Operation
```
User Input → Validation → Model Creation → Database Insert → Log Creation → Response
```

### 2. Read Operation
```
Request → Query Building → Database Select → Data Serialization → Response
```

### 3. Update Operation
```
User Input → Validation → Old Data Fetch → Model Update → Database Update → Log Creation → Response
```

### 4. Delete Operation
```
Request → Data Fetch → Log Creation → Database Delete → Response
```

## Security Considerations

### 1. Input Validation
- ✅ Validate tất cả input từ user
- ✅ Sanitize data trước khi lưu
- ✅ Use parameterized queries (SQLAlchemy tự động)

### 2. Access Control
- ✅ Implement authentication (có thể mở rộng)
- ✅ Role-based access control
- ✅ Audit logging cho mọi thay đổi

### 3. Data Protection
- ✅ Backup thường xuyên
- ✅ Encrypt sensitive data
- ✅ Secure file permissions

## Performance Considerations

### 1. Indexing Strategy
```sql
-- Index cho tìm kiếm
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_category ON products(category);

-- Index cho log queries
CREATE INDEX idx_logs_product_id ON product_logs(product_id);
CREATE INDEX idx_logs_created_at ON product_logs(created_at);
```

### 2. Query Optimization
- ✅ Use specific columns thay vì SELECT *
- ✅ Implement pagination cho large datasets
- ✅ Use database indexes hiệu quả
- ✅ Avoid N+1 queries với eager loading

### 3. Connection Management
- ✅ Use connection pooling
- ✅ Close connections properly
- ✅ Implement timeout handling

## Monitoring & Maintenance

### 1. Database Health Checks
- Monitor file size
- Check connection pool status
- Verify data integrity
- Monitor query performance

### 2. Backup Strategy
- Daily automated backups
- Test restore procedures
- Version control cho schema changes
- Document recovery procedures

### 3. Logging
- Query performance logs
- Error logging
- Access logging
- Change audit logs 