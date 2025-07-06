# 02. Models và Schema Design

## Tổng quan Models

Hệ thống sử dụng **SQLAlchemy ORM** với 2 models chính:

1. **Product** - Quản lý thông tin sản phẩm
2. **ProductLog** - Theo dõi lịch sử thay đổi

## 1. Product Model

### Định nghĩa Model

```python
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class Product(Base):
    """Model cho sản phẩm"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="Tên sản phẩm")
    sku = Column(String(100), unique=True, nullable=False, comment="Mã SKU")
    price = Column(Float, nullable=False, comment="Giá tiền")
    quantity = Column(Integer, default=0, comment="Số lượng trong kho")
    category = Column(String(100), comment="Nhóm/danh mục")
    description = Column(Text, comment="Mô tả sản phẩm")
    images = Column(JSON, default=list, comment="Danh sách đường dẫn ảnh")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Thời gian tạo")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Thời gian cập nhật")
    
    # Quan hệ với log
    logs = relationship("ProductLog", back_populates="product", cascade="all, delete-orphan")
```

### Chi tiết từng Field

#### 1.1 Primary Key
```python
id = Column(Integer, primary_key=True, index=True)
```
- **Type**: Integer (Auto-increment)
- **Constraint**: Primary Key
- **Index**: Tự động tạo index
- **Usage**: Định danh duy nhất cho sản phẩm

#### 1.2 Basic Information
```python
name = Column(String(255), nullable=False, comment="Tên sản phẩm")
sku = Column(String(100), unique=True, nullable=False, comment="Mã SKU")
```

**Name Field:**
- **Type**: String(255) - Đủ cho tên sản phẩm dài
- **Constraint**: NOT NULL - Bắt buộc phải có
- **Usage**: Hiển thị tên sản phẩm

**SKU Field:**
- **Type**: String(100) - Đủ cho mã SKU
- **Constraint**: UNIQUE + NOT NULL - Mã duy nhất, bắt buộc
- **Usage**: Mã định danh thương mại

#### 1.3 Financial & Inventory
```python
price = Column(Float, nullable=False, comment="Giá tiền")
quantity = Column(Integer, default=0, comment="Số lượng trong kho")
```

**Price Field:**
- **Type**: Float - Hỗ trợ số thập phân
- **Constraint**: NOT NULL
- **Usage**: Giá bán sản phẩm

**Quantity Field:**
- **Type**: Integer - Số nguyên
- **Default**: 0 - Mặc định không có hàng
- **Usage**: Số lượng tồn kho

#### 1.4 Classification
```python
category = Column(String(100), comment="Nhóm/danh mục")
description = Column(Text, comment="Mô tả sản phẩm")
```

**Category Field:**
- **Type**: String(100) - Đủ cho tên danh mục
- **Nullable**: Có thể NULL
- **Usage**: Phân loại sản phẩm

**Description Field:**
- **Type**: Text - Không giới hạn độ dài
- **Nullable**: Có thể NULL
- **Usage**: Mô tả chi tiết sản phẩm

#### 1.5 Media Storage
```python
images = Column(JSON, default=list, comment="Danh sách đường dẫn ảnh")
```

**Images Field:**
- **Type**: JSON - Lưu trữ array của strings
- **Default**: `[]` - Mảng rỗng
- **Usage**: Danh sách đường dẫn ảnh sản phẩm
- **Example**: `["image1.jpg", "image2.png"]`

#### 1.6 Timestamps
```python
created_at = Column(DateTime, default=datetime.utcnow, comment="Thời gian tạo")
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Thời gian cập nhật")
```

**Created At:**
- **Type**: DateTime
- **Default**: UTC time khi tạo
- **Usage**: Thời gian tạo sản phẩm

**Updated At:**
- **Type**: DateTime
- **Default**: UTC time khi tạo
- **On Update**: Tự động cập nhật khi thay đổi
- **Usage**: Thời gian cập nhật cuối cùng

#### 1.7 Relationships
```python
logs = relationship("ProductLog", back_populates="product", cascade="all, delete-orphan")
```

**Relationship:**
- **Type**: One-to-Many với ProductLog
- **Back Reference**: `product` trong ProductLog
- **Cascade**: Xóa log khi xóa sản phẩm

### Methods

#### 1.8 to_dict() Method
```python
def to_dict(self):
    """Chuyển đổi thành dictionary"""
    return {
        "id": self.id,
        "name": self.name,
        "sku": self.sku,
        "price": self.price,
        "quantity": self.quantity,
        "category": self.category,
        "description": self.description,
        "images": self.images or [],
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None
    }
```

**Usage:**
- Chuyển đổi model thành dictionary
- Serialize cho JSON response
- Format datetime thành ISO string

## 2. ProductLog Model

### Định nghĩa Model

```python
class ProductLog(Base):
    """Model cho log thay đổi sản phẩm"""
    __tablename__ = "product_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="ID sản phẩm")
    action = Column(String(50), nullable=False, comment="Hành động (create, update, delete)")
    field_name = Column(String(100), comment="Tên trường thay đổi")
    old_value = Column(Text, comment="Giá trị cũ")
    new_value = Column(Text, comment="Giá trị mới")
    changed_by = Column(String(100), default="admin", comment="Người thay đổi")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Thời gian thay đổi")
    
    # Quan hệ với sản phẩm
    product = relationship("Product", back_populates="logs")
```

### Chi tiết từng Field

#### 2.1 Primary Key
```python
id = Column(Integer, primary_key=True, index=True)
```
- **Type**: Integer (Auto-increment)
- **Usage**: Định danh duy nhất cho log entry

#### 2.2 Foreign Key
```python
product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="ID sản phẩm")
```
- **Type**: Integer
- **Foreign Key**: Tham chiếu đến `products.id`
- **Constraint**: NOT NULL
- **Usage**: Liên kết với sản phẩm

#### 2.3 Action Tracking
```python
action = Column(String(50), nullable=False, comment="Hành động (create, update, delete)")
```
- **Type**: String(50)
- **Constraint**: NOT NULL
- **Values**: "create", "update", "delete"
- **Usage**: Loại hành động được thực hiện

#### 2.4 Field Change Tracking
```python
field_name = Column(String(100), comment="Tên trường thay đổi")
old_value = Column(Text, comment="Giá trị cũ")
new_value = Column(Text, comment="Giá trị mới")
```

**Field Name:**
- **Type**: String(100)
- **Nullable**: Có thể NULL (cho create action)
- **Usage**: Tên field được thay đổi

**Old Value:**
- **Type**: Text - Không giới hạn độ dài
- **Nullable**: Có thể NULL
- **Usage**: Giá trị trước khi thay đổi

**New Value:**
- **Type**: Text - Không giới hạn độ dài
- **Nullable**: Có thể NULL
- **Usage**: Giá trị sau khi thay đổi

#### 2.5 User Tracking
```python
changed_by = Column(String(100), default="admin", comment="Người thay đổi")
```
- **Type**: String(100)
- **Default**: "admin"
- **Usage**: Người thực hiện thay đổi

#### 2.6 Timestamp
```python
created_at = Column(DateTime, default=datetime.utcnow, comment="Thời gian thay đổi")
```
- **Type**: DateTime
- **Default**: UTC time khi tạo log
- **Usage**: Thời gian thực hiện thay đổi

#### 2.7 Relationship
```python
product = relationship("Product", back_populates="logs")
```
- **Type**: Many-to-One với Product
- **Back Reference**: `logs` trong Product
- **Usage**: Truy cập thông tin sản phẩm từ log

### Methods

#### 2.8 to_dict() Method
```python
def to_dict(self):
    """Chuyển đổi thành dictionary"""
    return {
        "id": self.id,
        "product_id": self.product_id,
        "action": self.action,
        "field_name": self.field_name,
        "old_value": self.old_value,
        "new_value": self.new_value,
        "changed_by": self.changed_by,
        "created_at": self.created_at.isoformat() if self.created_at else None
    }
```

## 3. Database Schema SQL

### 3.1 Products Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
```

### 3.2 Product Logs Table
```sql
CREATE TABLE product_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100) DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
```

### 3.3 Indexes
```sql
-- Index cho products table
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_created_at ON products(created_at);

-- Index cho product_logs table
CREATE INDEX idx_product_logs_product_id ON product_logs(product_id);
CREATE INDEX idx_product_logs_action ON product_logs(action);
CREATE INDEX idx_product_logs_created_at ON product_logs(created_at);
```

## 4. Data Validation Rules

### 4.1 Product Validation
- **Name**: Required, max 255 characters
- **SKU**: Required, unique, max 100 characters
- **Price**: Required, positive number
- **Quantity**: Optional, non-negative integer
- **Category**: Optional, max 100 characters
- **Description**: Optional, unlimited text
- **Images**: Optional, JSON array of strings

### 4.2 ProductLog Validation
- **Product ID**: Required, must exist in products table
- **Action**: Required, must be "create", "update", or "delete"
- **Field Name**: Optional, max 100 characters
- **Old Value**: Optional, unlimited text
- **New Value**: Optional, unlimited text
- **Changed By**: Optional, max 100 characters, default "admin"

## 5. Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│   Product   │◄────────┤ ProductLog   │
│             │ 1:N     │              │
│ - id        │         │ - id         │
│ - name      │         │ - product_id │
│ - sku       │         │ - action     │
│ - price     │         │ - field_name │
│ - quantity  │         │ - old_value  │
│ - category  │         │ - new_value  │
│ - desc      │         │ - changed_by │
│ - images    │         │ - created_at │
│ - created   │         └──────────────┘
│ - updated   │
└─────────────┘
```

## 6. Usage Examples

### 6.1 Tạo sản phẩm mới
```python
product = Product(
    name="Laptop Dell",
    sku="DELL-001",
    price=15000000,
    quantity=10,
    category="Laptop",
    description="Laptop Dell Inspiron 15"
)
db.add(product)
db.commit()
```

### 6.2 Tạo log cho sản phẩm
```python
log = ProductLog(
    product_id=product.id,
    action="create",
    changed_by="admin"
)
db.add(log)
db.commit()
```

### 6.3 Query với relationship
```python
# Lấy sản phẩm và tất cả log
product = db.query(Product).filter(Product.id == 1).first()
logs = product.logs

# Lấy log và thông tin sản phẩm
log = db.query(ProductLog).filter(ProductLog.id == 1).first()
product_info = log.product
``` 