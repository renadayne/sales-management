# 🔍 Tính năng Tìm kiếm Sản phẩm

## 🎯 Mục tiêu
Thêm khả năng tìm kiếm sản phẩm theo tên hoặc SKU để người dùng dễ dàng tìm kiếm sản phẩm cần thiết.

## 📋 Yêu cầu chức năng

### Functional Requirements
- [x] Tìm kiếm theo tên sản phẩm
- [x] Tìm kiếm theo SKU
- [x] Tìm kiếm không phân biệt hoa thường
- [x] Hiển thị số lượng kết quả tìm được
- [x] Hiển thị thông báo khi không tìm thấy

### Non-Functional Requirements
- [x] Performance tốt với database lớn
- [x] Responsive design
- [x] UX mượt mà

## 🏗️ Thiết kế kỹ thuật

### 1. API Endpoint
```python
@app.get("/products")
async def get_products(
    request: Request,
    search: str = Query(None, description="Tìm kiếm theo tên hoặc SKU")
):
```

### 2. Database Query
```python
if search:
    search_filter = or_(
        Product.name.ilike(f"%{search}%"),
        Product.sku.ilike(f"%{search}%")
    )
    query = query.filter(search_filter)
```

### 3. Frontend Implementation
```html
<input type="text" class="form-control" name="search" 
       placeholder="Tìm kiếm theo tên hoặc SKU..." 
       value="{{ search or '' }}">
```

## 🔧 Implementation Details

### Backend Changes
- **File**: `app/routes/product.py`
- **Method**: GET `/products`
- **Parameter**: `search` (optional)
- **Logic**: SQL LIKE query với OR condition

### Frontend Changes
- **Input field**: Text input với placeholder
- **Form submission**: GET method để bookmark URL
- **Result display**: Counter + product list
- **Empty state**: "Không tìm thấy sản phẩm"

## 🧪 Testing

### Test Cases
1. **Tìm kiếm theo tên**: Nhập "phone" → Hiển thị sản phẩm có "phone" trong tên
2. **Tìm kiếm theo SKU**: Nhập "SKU001" → Hiển thị sản phẩm có SKU chứa "SKU001"
3. **Không tìm thấy**: Nhập từ khóa không tồn tại → Hiển thị thông báo
4. **Case insensitive**: "Phone" và "phone" cho kết quả giống nhau

## 📊 Performance
- **Index**: Cần index trên trường `name` và `sku`
- **Query optimization**: Sử dụng `ilike()` thay vì `like()`
- **Result limit**: Không giới hạn số lượng kết quả

## 🔄 Integration
- Tương thích với filter theo danh mục
- Giữ nguyên CRUD operations
- Không ảnh hưởng đến export Excel

## ✅ Checklist
- [x] Backend: Thêm parameter search
- [x] Backend: Logic tìm kiếm với OR condition
- [x] Frontend: Input field với placeholder
- [x] Frontend: Hiển thị kết quả và counter
- [x] Testing: Test các trường hợp cơ bản
- [x] Integration: Tương thích với features khác

---

**🎉 Feature đã hoàn thành trong v1.2!** 