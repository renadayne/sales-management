from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime, timedelta
from PIL import Image
import uuid

from app.database import get_db
from app.models import Product, ProductLog
from app.utils.export_excel import export_products_to_excel

router = APIRouter()

# Tạo thư mục uploads nếu chưa có
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_product_log(db: Session, product_id: int, action: str, field_name: str = None, 
                      old_value: str = None, new_value: str = None, changed_by: str = "admin"):
    """Tạo log thay đổi sản phẩm"""
    log = ProductLog(
        product_id=product_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by
    )
    db.add(log)
    db.commit()
    return log

def cleanup_old_logs(db: Session):
    """Xóa log cũ hơn 15 ngày"""
    cutoff_date = datetime.utcnow() - timedelta(days=15)
    db.query(ProductLog).filter(ProductLog.created_at < cutoff_date).delete()
    db.commit()

@router.get("/", response_class=HTMLResponse)
async def list_products(request: Request, search: str = "", category: str = "", message: str = "", db: Session = Depends(get_db)):
    """Hiển thị danh sách sản phẩm với tìm kiếm và filter theo danh mục"""
    # Xây dựng query base
    query = db.query(Product)
    
    # Filter theo danh mục
    if category:
        query = query.filter(Product.category == category)
    
    # Tìm kiếm sản phẩm theo tên hoặc SKU
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) | 
            (Product.sku.ilike(f"%{search}%"))
        )
    
    # Lấy danh sách sản phẩm
    products = query.order_by(Product.created_at.desc()).all()
    
    # Lấy danh sách danh mục để hiển thị trong dropdown
    categories = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()
    category_list = [cat[0] for cat in categories if cat[0]]
    
    # Kiểm tra sản phẩm có số lượng thấp
    low_stock_products = [p for p in products if p.quantity < 5]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1><i class="fas fa-box"></i> Sales Management</h1>
                <div>
                    <a href="/products/new" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Thêm sản phẩm
                    </a>
                    <a href="/products/export" class="btn btn-success">
                        <i class="fas fa-file-excel"></i> Xuất Excel
                    </a>
                </div>
            </div>
            
            <!-- Form tìm kiếm và filter -->
            <div class="row mb-4">
                <div class="col-md-8">
                    <form method="get" class="d-flex">
                        <input type="text" name="search" value="{search}" class="form-control me-2" 
                               placeholder="Tìm kiếm theo tên hoặc mã SKU...">
                        <select name="category" class="form-select me-2" style="min-width: 150px;">
                            <option value="">Tất cả danh mục</option>
                            {''.join([f'<option value="{cat}" {"selected" if cat == category else ""}>{cat}</option>' for cat in category_list])}
                        </select>
                        <button type="submit" class="btn btn-outline-primary">
                            <i class="fas fa-search"></i> Tìm
                        </button>
                        {f'<a href="/products" class="btn btn-outline-secondary ms-2">Xóa filter</a>' if search or category else ''}
                    </form>
                </div>
                <div class="col-md-4 text-end">
                    <span class="text-muted">Tìm thấy {len(products)} sản phẩm</span>
                </div>
            </div>
            
            {f'<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Có {len(low_stock_products)} sản phẩm có số lượng dưới 5!</div>' if low_stock_products else ''}
            
            {f'<div class="alert alert-success"><i class="fas fa-check-circle"></i> {message}</div>' if message else ''}
            
            {f'<div class="alert alert-info"><i class="fas fa-search"></i> Kết quả tìm kiếm cho: "{search}"</div>' if search else ''}
            
            {f'<div class="alert alert-info"><i class="fas fa-filter"></i> Đang lọc theo danh mục: "{category}"</div>' if category else ''}
            
            {f'<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Không tìm thấy sản phẩm nào phù hợp với điều kiện tìm kiếm</div>' if (search or category) and not products else ''}
            
            <div class="row">
                {''.join([f'''
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">{product.name}</h5>
                            <p class="card-text">
                                <strong>SKU:</strong> {product.sku}<br>
                                <strong>Giá:</strong> {product.price:,.0f} VNĐ<br>
                                <strong>Số lượng:</strong> 
                                <span class="{'text-danger' if product.quantity < 5 else 'text-success'}">
                                    {product.quantity}
                                </span><br>
                                <strong>Danh mục:</strong> {product.category or 'N/A'}<br>
                                <strong>Mô tả:</strong> {product.description or 'N/A'}
                            </p>
                            {f'<div class="mb-2"><img src="/static/uploads/{product.images[0]}" class="img-thumbnail" style="max-height: 100px;"></div>' if product.images else ''}
                        </div>
                        <div class="card-footer">
                            <a href="/products/{product.id}/edit" class="btn btn-sm btn-warning">
                                <i class="fas fa-edit"></i> Sửa
                            </a>
                            <a href="/products/{product.id}/logs" class="btn btn-sm btn-info">
                                <i class="fas fa-history"></i> Lịch sử
                            </a>
                            <button onclick="deleteProduct({product.id})" class="btn btn-sm btn-danger">
                                <i class="fas fa-trash"></i> Xóa
                            </button>
                        </div>
                    </div>
                </div>
                ''' for product in products])}
            </div>
        </div>
        
        <script>
        function deleteProduct(id) {{
            if (confirm('Bạn có chắc muốn xóa sản phẩm này?')) {{
                fetch(`/products/${{id}}`, {{method: 'DELETE'}})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            location.reload();
                        }} else {{
                            alert('Có lỗi xảy ra: ' + data.message);
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        alert('Có lỗi xảy ra khi xóa sản phẩm');
                    }});
            }}
        }}
        </script>
    </body>
    </html>
    """

@router.get("/new", response_class=HTMLResponse)
async def new_product_form():
    """Form thêm sản phẩm mới"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Thêm sản phẩm mới</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1><i class="fas fa-plus"></i> Thêm sản phẩm mới</h1>
            <form action="/products" method="post" enctype="multipart/form-data">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Tên sản phẩm *</label>
                            <input type="text" name="name" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Mã SKU *</label>
                            <input type="text" name="sku" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Giá tiền *</label>
                            <input type="number" name="price" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Số lượng trong kho</label>
                            <input type="number" name="quantity" class="form-control" value="0">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Danh mục</label>
                            <input type="text" name="category" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Mô tả</label>
                            <textarea name="description" class="form-control" rows="3"></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Ảnh sản phẩm (tối đa 5 ảnh)</label>
                            <input type="file" name="images" class="form-control" multiple accept=".jpg,.jpeg,.png,.webp">
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <button type="submit" class="btn btn-primary">Thêm sản phẩm</button>
                    <a href="/products" class="btn btn-secondary">Hủy</a>
                </div>
            </form>
        </div>
    </body>
    </html>
    """

@router.post("/")
async def create_product(
    name: str = Form(...),
    sku: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(0),
    category: str = Form(""),
    description: str = Form(""),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    """Tạo sản phẩm mới"""
    # Kiểm tra SKU đã tồn tại
    existing_product = db.query(Product).filter(Product.sku == sku).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="SKU đã tồn tại")
    
    # Xử lý upload ảnh
    image_paths = []
    for image in images[:5]:  # Giới hạn 5 ảnh
        if image.filename:
            # Tạo tên file unique
            file_ext = os.path.splitext(image.filename)[1]
            filename = f"{uuid.uuid4()}{file_ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            # Lưu file
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            image_paths.append(filename)
    
    # Tạo sản phẩm
    product = Product(
        name=name,
        sku=sku,
        price=price,
        quantity=quantity,
        category=category,
        description=description,
        images=image_paths
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Tạo log
    create_product_log(db, product.id, "create", changed_by="admin")
    
    return RedirectResponse(url="/products?message=Sản phẩm đã được tạo thành công!", status_code=303)

@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(product_id: int, db: Session = Depends(get_db)):
    """Form sửa sản phẩm"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sửa sản phẩm</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1><i class="fas fa-edit"></i> Sửa sản phẩm</h1>
            <form action="/products/{product_id}" method="post" enctype="multipart/form-data">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Tên sản phẩm *</label>
                            <input type="text" name="name" class="form-control" value="{product.name}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Mã SKU *</label>
                            <input type="text" name="sku" class="form-control" value="{product.sku}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Giá tiền *</label>
                            <input type="number" name="price" class="form-control" value="{product.price}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Số lượng trong kho</label>
                            <input type="number" name="quantity" class="form-control" value="{product.quantity}">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Danh mục</label>
                            <input type="text" name="category" class="form-control" value="{product.category or ''}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Mô tả</label>
                            <textarea name="description" class="form-control" rows="3">{product.description or ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Ảnh hiện tại</label>
                            <div class="mb-2">
                                {''.join([f'<img src="/static/uploads/{img}" class="img-thumbnail me-2" style="max-height: 80px;">' for img in product.images])}
                            </div>
                            <input type="file" name="images" class="form-control" multiple accept=".jpg,.jpeg,.png,.webp">
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <button type="submit" class="btn btn-primary">Cập nhật</button>
                    <a href="/products" class="btn btn-secondary">Hủy</a>
                </div>
            </form>
        </div>
    </body>
    </html>
    """

@router.post("/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    sku: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(0),
    category: str = Form(""),
    description: str = Form(""),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    """Cập nhật sản phẩm"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    # Kiểm tra SKU đã tồn tại (trừ sản phẩm hiện tại)
    existing_product = db.query(Product).filter(Product.sku == sku, Product.id != product_id).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="SKU đã tồn tại")
    
    # Lưu giá trị cũ để log
    old_values = {
        "name": product.name,
        "sku": product.sku,
        "price": product.price,
        "quantity": product.quantity,
        "category": product.category,
        "description": product.description
    }
    
    # Cập nhật thông tin
    product.name = name
    product.sku = sku
    product.price = price
    product.quantity = quantity
    product.category = category
    product.description = description
    
    # Xử lý upload ảnh mới
    if images and any(image.filename for image in images):
        image_paths = []
        for image in images[:5]:
            if image.filename:
                file_ext = os.path.splitext(image.filename)[1]
                filename = f"{uuid.uuid4()}{file_ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                
                image_paths.append(filename)
        
        # Chỉ cập nhật ảnh nếu có ảnh mới upload
        if image_paths:
            product.images = image_paths
    
    db.commit()
    
    # Tạo log cho từng thay đổi
    for field, old_value in old_values.items():
        new_value = getattr(product, field)
        if str(old_value) != str(new_value):
            create_product_log(
                db, product.id, "update", field, 
                str(old_value), str(new_value), "admin"
            )
    
    return RedirectResponse(url="/products?message=Sản phẩm đã được cập nhật thành công!", status_code=303)

@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Xóa sản phẩm"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    # Xóa ảnh
    for image in product.images:
        image_path = os.path.join(UPLOAD_DIR, image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Tạo log trước khi xóa
    create_product_log(db, product_id, "delete", changed_by="admin")
    
    # Xóa sản phẩm
    db.delete(product)
    db.commit()
    
    return {"success": True, "message": "Sản phẩm đã được xóa thành công"}

@router.get("/{product_id}/logs", response_class=HTMLResponse)
async def product_logs(product_id: int, db: Session = Depends(get_db)):
    """Hiển thị lịch sử thay đổi sản phẩm"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    logs = db.query(ProductLog).filter(ProductLog.product_id == product_id).order_by(ProductLog.created_at.desc()).all()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lịch sử thay đổi - {product.name}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1><i class="fas fa-history"></i> Lịch sử thay đổi: {product.name}</h1>
            <a href="/products" class="btn btn-secondary mb-3">← Quay lại</a>
            
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Thời gian</th>
                            <th>Hành động</th>
                            <th>Trường thay đổi</th>
                            <th>Giá trị cũ</th>
                            <th>Giá trị mới</th>
                            <th>Người thay đổi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''}</td>
                            <td>
                                <span class="badge bg-{'success' if log.action == 'create' else 'warning' if log.action == 'update' else 'danger'}">
                                    {log.action}
                                </span>
                            </td>
                            <td>{log.field_name or '-'}</td>
                            <td>{log.old_value or '-'}</td>
                            <td>{log.new_value or '-'}</td>
                            <td>{log.changed_by}</td>
                        </tr>
                        ''' for log in logs])}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

@router.get("/export")
async def export_excel(db: Session = Depends(get_db)):
    """Xuất dữ liệu ra file Excel"""
    # Dọn dẹp log cũ
    cleanup_old_logs(db)
    
    # Lấy dữ liệu
    products = db.query(Product).all()
    logs = db.query(ProductLog).all()
    
    # Xuất Excel
    filename = f"products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = export_products_to_excel(products, logs, filename)
    
    return FileResponse(filepath, filename=filename) 