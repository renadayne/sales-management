# 📋 Tính năng Filter theo Danh mục Sản phẩm

## 🎯 Mục tiêu
Thêm khả năng lọc sản phẩm theo danh mục để người dùng dễ dàng tìm kiếm và quản lý sản phẩm theo nhóm.

## 📋 Yêu cầu chức năng

### Functional Requirements
- [x] Hiển thị dropdown chọn danh mục
- [x] Lọc sản phẩm theo danh mục được chọn
- [x] Kết hợp với tính năng tìm kiếm hiện có
- [x] Hiển thị số lượng sản phẩm tìm được
- [x] Nút "Xóa bộ lọc" để reset
- [x] Giữ nguyên trạng thái filter khi thao tác CRUD

### Non-Functional Requirements
- [x] Responsive design trên mobile
- [x] Performance tốt với database lớn
- [x] UX mượt mà, không reload page
- [x] Tương thích với tính năng tìm kiếm hiện có

## 🏗️ Thiết kế kỹ thuật

### 1. Database Schema
Không cần thay đổi database schema vì trường `category` đã có sẵn trong bảng `products`.

```sql
-- Trường category trong bảng products
category VARCHAR(50) NOT NULL DEFAULT 'Khác'
```

### 2. API Endpoint
Cập nhật endpoint `/products` để hỗ trợ parameter `category`:

```python
@app.get("/products")
async def get_products(
    request: Request,
    search: str = Query(None, description="Tìm kiếm theo tên hoặc SKU"),
    category: str = Query(None, description="Lọc theo danh mục")
):
    # Logic xử lý filter
```

### 3. Frontend Components
- **Dropdown danh mục**: Bootstrap select component
- **Kết hợp tìm kiếm**: Form với 2 input fields
- **Hiển thị kết quả**: Counter + danh sách sản phẩm
- **Reset button**: Clear tất cả filter

## 🔧 Implementation Details

### 1. Backend Changes

#### File: `app/routes/product.py`

**Thêm parameter category vào endpoint:**
```python
@app.get("/products")
async def get_products(
    request: Request,
    search: str = Query(None, description="Tìm kiếm theo tên hoặc SKU"),
    category: str = Query(None, description="Lọc theo danh mục")
):
```

**Logic filter kết hợp:**
```python
# Xây dựng query với filter
query = db.query(Product)

# Filter theo danh mục
if category and category != "Tất cả":
    query = query.filter(Product.category == category)

# Kết hợp với tìm kiếm
if search:
    search_filter = or_(
        Product.name.ilike(f"%{search}%"),
        Product.sku.ilike(f"%{search}%")
    )
    query = query.filter(search_filter)
```

### 2. Frontend Changes

#### File: `app/routes/product.py` (HTML template)

**Thêm dropdown danh mục:**
```html
<div class="row mb-3">
    <div class="col-md-6">
        <input type="text" class="form-control" name="search" 
               placeholder="Tìm kiếm theo tên hoặc SKU..." 
               value="{{ search or '' }}">
    </div>
    <div class="col-md-4">
        <select class="form-control" name="category">
            <option value="">Tất cả danh mục</option>
            <option value="Điện tử" {{ 'selected' if category == 'Điện tử' else '' }}>Điện tử</option>
            <option value="Thời trang" {{ 'selected' if category == 'Thời trang' else '' }}>Thời trang</option>
            <option value="Gia dụng" {{ 'selected' if category == 'Gia dụng' else '' }}>Gia dụng</option>
            <option value="Sách" {{ 'selected' if category == 'Sách' else '' }}>Sách</option>
            <option value="Thể thao" {{ 'selected' if category == 'Thể thao' else '' }}>Thể thao</option>
            <option value="Khác" {{ 'selected' if category == 'Khác' else '' }}>Khác</option>
        </select>
    </div>
    <div class="col-md-2">
        <button type="submit" class="btn btn-primary w-100">Tìm kiếm</button>
    </div>
</div>
```

**Hiển thị kết quả và nút reset:**
```html
{% if search or category %}
<div class="alert alert-info">
    <strong>Kết quả tìm kiếm:</strong> {{ products|length }} sản phẩm
    {% if search %} - Từ khóa: "{{ search }}"{% endif %}
    {% if category and category != "Tất cả" %} - Danh mục: {{ category }}{% endif %}
    <a href="/products" class="btn btn-sm btn-outline-secondary float-right">Xóa bộ lọc</a>
</div>
{% endif %}
```

### 3. Data Flow

```
User Input → Form Submit → Backend Filter → Database Query → Results → Template Render
     ↓              ↓              ↓              ↓              ↓              ↓
Dropdown    →   GET /products  →  SQLAlchemy  →  SQLite     →  Products   →  HTML
Search      →   ?category=...  →  Filter      →  Query      →  List       →  Display
```

## 🧪 Testing

### Test Cases

1. **Filter theo danh mục đơn lẻ:**
   - Chọn "Điện tử" → Hiển thị chỉ sản phẩm điện tử
   - Chọn "Thời trang" → Hiển thị chỉ sản phẩm thời trang

2. **Kết hợp tìm kiếm và filter:**
   - Tìm "phone" + chọn "Điện tử" → Kết quả giao nhau
   - Tìm "áo" + chọn "Thời trang" → Kết quả giao nhau

3. **Reset filter:**
   - Click "Xóa bộ lọc" → Hiển thị tất cả sản phẩm
   - URL trở về `/products` (không có parameter)

4. **Edge cases:**
   - Không có sản phẩm nào trong danh mục → Hiển thị "Không tìm thấy"
   - Filter + search không có kết quả → Hiển thị thông báo phù hợp

## 📊 Performance Considerations

### Database Optimization
- **Index**: Đã có index trên trường `category` (nếu chưa có thì cần thêm)
- **Query efficiency**: Sử dụng `filter()` thay vì `filter_by()` để tối ưu
- **Combined filters**: Sử dụng `and_()` để kết hợp nhiều điều kiện

### Frontend Optimization
- **Form submission**: Sử dụng GET method để có thể bookmark URL
- **Caching**: Browser cache cho static assets
- **Responsive**: Bootstrap grid system cho mobile

## 🔄 Integration với tính năng hiện có

### 1. Tương thích với Search
- Giữ nguyên logic tìm kiếm hiện có
- Thêm filter category vào query builder
- Kết hợp cả 2 điều kiện bằng `and_()`

### 2. Tương thích với CRUD
- Giữ nguyên form thêm/sửa sản phẩm
- Không ảnh hưởng đến validation
- Redirect về trang danh sách với filter hiện tại

### 3. Tương thích với Export Excel
- Export tất cả sản phẩm (không theo filter)
- Hoặc có thể thêm option export theo filter (future enhancement)

## 🚀 Deployment

### Files Modified
- `app/routes/product.py` - Thêm parameter và logic filter

### Files Added
- `docs/features/filter-by-category.md` - Tài liệu này

### Database Changes
- Không cần migration vì trường `category` đã có sẵn

## 📈 Future Enhancements

### Potential Improvements
1. **Multi-select categories**: Chọn nhiều danh mục cùng lúc
2. **Advanced filters**: Filter theo giá, số lượng, ngày tạo
3. **Saved filters**: Lưu filter yêu thích
4. **Export filtered data**: Xuất Excel theo filter hiện tại
5. **Category management**: CRUD danh mục (admin feature)

### Technical Debt
- Có thể tách logic filter thành service class riêng
- Có thể thêm unit tests cho filter logic
- Có thể cache danh sách categories

## 📝 Commit History

```
commit: Add category filter feature
- Add category parameter to /products endpoint
- Add dropdown category filter in frontend
- Combine search and category filters
- Add result counter and reset button
- Update documentation
```

## ✅ Checklist

- [x] Backend: Thêm parameter category
- [x] Backend: Logic filter kết hợp với search
- [x] Frontend: Dropdown danh mục
- [x] Frontend: Form kết hợp search + category
- [x] Frontend: Hiển thị số lượng kết quả
- [x] Frontend: Nút "Xóa bộ lọc"
- [x] Testing: Test các trường hợp cơ bản
- [x] Documentation: Tài liệu kỹ thuật
- [x] Integration: Tương thích với tính năng hiện có

---

**🎉 Feature đã hoàn thành và sẵn sàng deploy!** 