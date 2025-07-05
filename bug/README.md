# 🐛 Bug Tracking

Thư mục này chứa tài liệu về các bug đã phát hiện và cách fix.

## 📋 **Quy ước đặt tên file**

```
### Format: `{số thứ tự}-{mô tả ngắn}.md`

Ví dụ:
- `001-image-disappear-on-edit.md`
- `002-search-not-working.md`
- `003-export-excel-error.md`
```

## 📝 **Template cho bug mới**

```markdown
# Bug #{số}: {Tên bug}

## 🐛 **Mô tả bug**
- **Ngày phát hiện**: {DD/MM/YYYY}
- **Mức độ**: {Low/Medium/High/Critical}
- **Trạng thái**: {🔄 Đang fix / ✅ Đã fix / ❌ Không fix}

### **Triệu chứng**
1. {Mô tả bước 1}
2. {Mô tả bước 2}
3. **Kết quả**: {Mô tả lỗi}

### **Cách tái hiện**
1. {Bước 1}
2. {Bước 2}
3. {Bước 3}
4. **Kết quả**: {Lỗi xuất hiện}

---

## 🔍 **Nguyên nhân**
{Giải thích nguyên nhân gây ra bug}

---

## ✅ **Giải pháp**
{Giải thích cách fix}

---

## 🧪 **Test case**
{Liệt kê các test case để verify fix}

---

## 📝 **File thay đổi**
- **File**: {đường dẫn file}
- **Function**: {tên function}
- **Dòng**: {số dòng}

---

**Người fix**: {Tên người fix}  
**Ngày fix**: {DD/MM/YYYY}  
**Commit**: {hash commit}
```

## 🎯 **Mức độ bug**

| Mức độ | Mô tả | Ví dụ |
|--------|-------|-------|
| **Low** | Bug nhỏ, không ảnh hưởng chức năng chính | Typo, UI nhỏ |
| **Medium** | Bug ảnh hưởng một phần chức năng | Upload ảnh, search |
| **High** | Bug ảnh hưởng chức năng chính | CRUD sản phẩm |
| **Critical** | Bug làm crash hệ thống | Database error |

## 📊 **Thống kê**

- **Tổng số bug**: 1
- **Đã fix**: 1
- **Đang fix**: 0
- **Không fix**: 0

## 📚 **Danh sách bug**

| # | Tên | Mức độ | Trạng thái | Ngày |
|---|-----|--------|------------|------|
| 001 | Ảnh biến mất khi sửa sản phẩm | Medium | ✅ Đã fix | 07/06/2025 |

---

**Lưu ý**: 
- Luôn cập nhật trạng thái bug sau khi fix
- Ghi chép đầy đủ để tránh lặp lại
- Test kỹ trước khi đánh dấu "Đã fix" 