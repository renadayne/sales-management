# Tài liệu Database - Hệ thống Quản lý Bán hàng

## Tổng quan

Hệ thống Quản lý Bán hàng sử dụng **SQLite** làm cơ sở dữ liệu chính với **SQLAlchemy ORM** để quản lý dữ liệu. Database được thiết kế đơn giản nhưng hiệu quả, phù hợp cho ứng dụng quản lý sản phẩm với các tính năng CRUD, tìm kiếm, lọc và theo dõi lịch sử thay đổi.

## Cấu trúc tài liệu

- **[01-overview.md](./01-overview.md)** - Tổng quan về kiến trúc database
- **[02-models.md](./02-models.md)** - Chi tiết các model và schema
- **[03-connection.md](./03-connection.md)** - Cấu hình kết nối database
- **[04-operations.md](./04-operations.md)** - Các thao tác CRUD và query
- **[05-migration.md](./05-migration.md)** - Hướng dẫn migration và backup
- **[06-performance.md](./06-performance.md)** - Tối ưu hiệu suất database
- **[07-troubleshooting.md](./07-troubleshooting.md)** - Xử lý sự cố thường gặp

## Đặc điểm chính

### 🗄️ Database Engine
- **SQLite**: Database file-based, không cần server riêng
- **SQLAlchemy**: ORM mạnh mẽ với type safety
- **Alembic**: Migration tool (có thể mở rộng)

### 📊 Schema Design
- **2 bảng chính**: `products`, `product_logs`
- **Quan hệ 1-n**: Product ↔ ProductLog
- **JSON field**: Lưu trữ danh sách ảnh
- **Audit trail**: Theo dõi mọi thay đổi

### 🔧 Tính năng
- **CRUD operations**: Đầy đủ thao tác cơ bản
- **Search & Filter**: Tìm kiếm theo tên/SKU, lọc theo danh mục
- **Image management**: Upload và quản lý ảnh sản phẩm
- **Export Excel**: Xuất dữ liệu ra file Excel
- **Logging**: Ghi lại lịch sử thay đổi

## Cấu trúc thư mục

```
sales-management/
├── app/
│   ├── database.py          # Cấu hình kết nối DB
│   └── models.py           # Định nghĩa models
├── data/
│   └── sales_management.db # File database SQLite
├── init_db.py              # Script khởi tạo DB
└── docs/database/          # Tài liệu database
```

## Quick Start

1. **Khởi tạo database**:
   ```bash
   python init_db.py
   ```

2. **Chạy ứng dụng**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. **Truy cập**: http://localhost:8000/products

## Yêu cầu hệ thống

- Python 3.7+
- SQLAlchemy 1.4+
- SQLite3 (built-in Python)
- FastAPI (web framework)

## Lưu ý quan trọng

- Database file được lưu tại `./data/sales_management.db`
- Backup thường xuyên file database
- Kiểm tra quyền ghi trong thư mục `data/`
- Monitor kích thước file database khi có nhiều ảnh 