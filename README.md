# 🛍️ Hệ thống Quản lý Bán hàng Nội bộ

Hệ thống web đơn giản để quản lý sản phẩm và kho hàng trong môi trường nội bộ, chạy local, dùng trong nhóm nhỏ.

## ✨ Tính năng chính

### 📦 Quản lý sản phẩm
- ✅ Thêm, sửa, xóa sản phẩm
- ✅ Quản lý thông tin: tên, SKU, giá, số lượng, danh mục, mô tả
- ✅ Upload ảnh sản phẩm (tối đa 5 ảnh/sản phẩm)
- ✅ Hỗ trợ định dạng: JPG, PNG, WEBP

### 📊 Quản lý kho
- ✅ Theo dõi số lượng sản phẩm
- ✅ Cảnh báo sản phẩm có số lượng < 5
- ✅ Chỉnh sửa số lượng dễ dàng

### 📝 Lịch sử chỉnh sửa
- ✅ Lưu log mọi thay đổi (ai, lúc nào, thay đổi gì)
- ✅ Tự động xóa log sau 15 ngày
- ✅ Xem lịch sử chi tiết từng sản phẩm

### 📄 Xuất dữ liệu
- ✅ Xuất toàn bộ sản phẩm + lịch sử ra file Excel
- ✅ Backup dữ liệu trước khi log bị xóa

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | Python + FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Frontend | HTML + Bootstrap |
| Upload ảnh | Lưu local vào `static/uploads/` |
| Export Excel | openpyxl |

## 🚀 Cài đặt và chạy

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Khởi tạo database và dữ liệu mẫu
```bash
python init_db.py
```

### 3. Chạy ứng dụng
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Truy cập hệ thống
Mở trình duyệt và truy cập: **http://localhost:8000**

## 📁 Cấu trúc dự án

```
sales-management/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app chính
│   ├── database.py          # Cấu hình database
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── product.py       # API endpoints
│   └── utils/
│       ├── __init__.py
│       └── export_excel.py  # Xuất Excel
├── static/
│   └── uploads/             # Thư mục lưu ảnh
├── data/
│   └── sales_management.db  # SQLite database
├── exports/                 # Thư mục xuất Excel
├── requirements.txt
├── init_db.py
└── README.md
```

## 🎯 Hướng dẫn sử dụng

### Quản lý sản phẩm
1. **Xem danh sách**: Truy cập `/products`
2. **Thêm sản phẩm**: Click "Thêm sản phẩm" → Điền thông tin → Upload ảnh
3. **Sửa sản phẩm**: Click "Sửa" trên card sản phẩm
4. **Xóa sản phẩm**: Click "Xóa" → Xác nhận

### Xem lịch sử
- Click "Lịch sử" trên card sản phẩm để xem log thay đổi
- Log tự động xóa sau 15 ngày

### Xuất Excel
- Click "Xuất Excel" để tải file Excel với 2 sheet:
  - Sheet 1: Danh sách sản phẩm
  - Sheet 2: Lịch sử thay đổi

## 🔧 Cấu hình

### Database
- Sử dụng SQLite, file lưu tại `data/sales_management.db`
- Tự động tạo khi chạy lần đầu

### Upload ảnh
- Lưu tại `static/uploads/`
- Hỗ trợ: JPG, JPEG, PNG, WEBP
- Tối đa 5 ảnh/sản phẩm

### Log tự động xóa
- Log cũ hơn 15 ngày tự động xóa
- Chạy mỗi lần xuất Excel

## 🛡️ Bảo mật

- Hệ thống dùng nội bộ, không mở public
- Không có authentication phức tạp
- Dữ liệu lưu local, không gửi lên cloud

## 📊 Database Schema

### Bảng `products`
- `id`: Primary key
- `name`: Tên sản phẩm
- `sku`: Mã SKU (unique)
- `price`: Giá tiền
- `quantity`: Số lượng trong kho
- `category`: Danh mục
- `description`: Mô tả
- `images`: JSON array đường dẫn ảnh
- `created_at`: Thời gian tạo
- `updated_at`: Thời gian cập nhật

### Bảng `product_logs`
- `id`: Primary key
- `product_id`: Foreign key đến products
- `action`: Hành động (create/update/delete)
- `field_name`: Tên trường thay đổi
- `old_value`: Giá trị cũ
- `new_value`: Giá trị mới
- `changed_by`: Người thay đổi
- `created_at`: Thời gian thay đổi

## 🐛 Xử lý lỗi thường gặp

### Lỗi import
```bash
# Nếu lỗi import, thử:
pip install --upgrade pip
pip install -r requirements.txt
```

### Lỗi database
```bash
# Xóa file database cũ và tạo lại:
rm data/sales_management.db
python init_db.py
```

### Lỗi upload ảnh
- Kiểm tra thư mục `static/uploads/` có quyền ghi
- Đảm bảo file ảnh đúng định dạng

## 📞 Hỗ trợ

Hệ thống được thiết kế đơn giản, dễ sử dụng cho nhóm nhỏ. Nếu có vấn đề, kiểm tra:
1. Log console khi chạy ứng dụng
2. File database có tồn tại không
3. Thư mục uploads có quyền ghi không

---

**🎉 Chúc bạn sử dụng hệ thống hiệu quả!**