# Bug #001: Ảnh biến mất khi sửa sản phẩm

## 🐛 **Mô tả bug**
- **Ngày phát hiện**: 07/06/2025
- **Mức độ**: Medium
- **Trạng thái**: ✅ Đã fix

### **Triệu chứng**
1. Upload ảnh sản phẩm thành công → Ảnh hiển thị bình thường
2. Sửa sản phẩm (không upload ảnh mới) → Ảnh vẫn hiển thị ✅
3. **Sửa sản phẩm lần thứ 2** (không upload ảnh mới) → Ảnh biến mất ❌

### **Cách tái hiện**
1. Thêm sản phẩm mới với ảnh
2. Sửa sản phẩm (không thay đổi ảnh) → Cập nhật
3. Sửa sản phẩm lần nữa (không thay đổi ảnh) → Cập nhật
4. **Kết quả**: Ảnh biến mất khỏi danh sách sản phẩm

---

## 🔍 **Nguyên nhân**

### **Code cũ (có bug)**
```python
# Xử lý upload ảnh mới
if images:  # ❌ Luôn true vì File([]) trả về list rỗng
    image_paths = []
    for image in images[:5]:
        if image.filename:
            # ... xử lý upload
            image_paths.append(filename)
    
    product.images = image_paths  # ❌ Ghi đè thành list rỗng
```

### **Vấn đề**
- `images: List[UploadFile] = File([])` luôn trả về list rỗng khi không upload file
- `if images:` luôn true → luôn chạy vào block xử lý
- `product.images = image_paths` ghi đè ảnh cũ thành list rỗng

---

## ✅ **Giải pháp**

### **Code mới (đã fix)**
```python
# Xử lý upload ảnh mới
if images and any(image.filename for image in images):  # ✅ Chỉ true khi có file thực sự
    image_paths = []
    for image in images[:5]:
        if image.filename:
            # ... xử lý upload
            image_paths.append(filename)
    
    # Chỉ cập nhật ảnh nếu có ảnh mới upload
    if image_paths:  # ✅ Thêm check bảo vệ
        product.images = image_paths
```

### **Thay đổi chính**
1. **`if images and any(image.filename for image in images):`**
   - Kiểm tra có file thực sự được upload
   - Tránh chạy vào block khi không có file

2. **`if image_paths:`**
   - Thêm check bảo vệ cuối cùng
   - Chỉ cập nhật khi có ảnh mới

---

## 🧪 **Test case**

### **Test 1: Upload ảnh mới**
- ✅ Thêm sản phẩm với ảnh → Ảnh hiển thị
- ✅ Sửa sản phẩm, upload ảnh mới → Ảnh mới thay thế

### **Test 2: Giữ nguyên ảnh**
- ✅ Thêm sản phẩm với ảnh → Ảnh hiển thị  
- ✅ Sửa sản phẩm (không upload) → Ảnh vẫn giữ nguyên
- ✅ Sửa sản phẩm lần nữa (không upload) → Ảnh vẫn giữ nguyên

### **Test 3: Xóa ảnh**
- ✅ Thêm sản phẩm với ảnh → Ảnh hiển thị
- ✅ Sửa sản phẩm, upload ảnh mới → Ảnh mới thay thế
- ✅ Sửa sản phẩm, không upload → Ảnh mới vẫn giữ nguyên

---

## 📝 **File thay đổi**
- **File**: `app/routes/product.py`
- **Function**: `update_product()`
- **Dòng**: 365-375

### **Diff**
```diff
- if images:
+ if images and any(image.filename for image in images):
    # ... xử lý upload
+ if image_paths:
        product.images = image_paths
```

---

## 🎯 **Kết quả**
- ✅ Fix hoàn toàn bug ảnh biến mất
- ✅ Giữ nguyên ảnh cũ khi không upload mới
- ✅ Thay thế ảnh khi upload mới
- ✅ Không ảnh hưởng đến tính năng khác

---

## 📚 **Bài học**
1. **Kiểm tra điều kiện kỹ**: `File([])` luôn trả về list rỗng, không phải `None`
2. **Thêm check bảo vệ**: Luôn kiểm tra dữ liệu trước khi ghi đè
3. **Test nhiều lần**: Bug chỉ xuất hiện sau lần sửa thứ 2
4. **Log rõ ràng**: Ghi chép bug để tránh lặp lại

---

**Người fix**: AI Assistant  
**Ngày fix**: 07/06/2025  
**Commit**: `feat: Fix image disappear bug on product edit` 