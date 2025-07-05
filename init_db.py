#!/usr/bin/env python3
"""
Script khởi tạo database và thêm dữ liệu mẫu
"""

import os
import sys
from datetime import datetime

# Thêm thư mục gốc vào path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models import Product, ProductLog

def create_sample_data():
    """Tạo dữ liệu mẫu cho hệ thống"""
    db = SessionLocal()
    
    try:
        # Kiểm tra xem đã có dữ liệu chưa
        existing_products = db.query(Product).count()
        if existing_products > 0:
            print("⚠️  Database đã có dữ liệu, bỏ qua việc tạo dữ liệu mẫu")
            return
        
        # Tạo sản phẩm mẫu
        sample_products = [
            {
                "name": "Laptop Dell Inspiron 15",
                "sku": "DELL-INS15-001",
                "price": 15000000,
                "quantity": 10,
                "category": "Laptop",
                "description": "Laptop Dell Inspiron 15 inch, Intel i5, 8GB RAM, 256GB SSD"
            },
            {
                "name": "Chuột không dây Logitech",
                "sku": "LOG-MOUSE-001",
                "price": 500000,
                "quantity": 25,
                "category": "Phụ kiện",
                "description": "Chuột không dây Logitech M185, pin AA"
            },
            {
                "name": "Bàn phím cơ Keychron K2",
                "sku": "KEY-K2-001",
                "price": 2500000,
                "quantity": 3,
                "category": "Phụ kiện",
                "description": "Bàn phím cơ Keychron K2, switch Brown, RGB"
            },
            {
                "name": "Màn hình LG 24 inch",
                "sku": "LG-24-001",
                "price": 3500000,
                "quantity": 8,
                "category": "Màn hình",
                "description": "Màn hình LG 24 inch Full HD, IPS"
            },
            {
                "name": "Tai nghe Sony WH-1000XM4",
                "sku": "SONY-WH4-001",
                "price": 8000000,
                "quantity": 2,
                "category": "Âm thanh",
                "description": "Tai nghe chống ồn Sony WH-1000XM4"
            }
        ]
        
        print("📦 Đang tạo dữ liệu mẫu...")
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.add(product)
            db.commit()
            db.refresh(product)
            
            # Tạo log cho sản phẩm mới
            log = ProductLog(
                product_id=product.id,
                action="create",
                changed_by="admin"
            )
            db.add(log)
            
            print(f"✅ Đã tạo sản phẩm: {product.name}")
        
        db.commit()
        print(f"🎉 Đã tạo thành công {len(sample_products)} sản phẩm mẫu!")
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo dữ liệu mẫu: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Hàm chính"""
    print("🚀 Khởi tạo hệ thống Quản lý Bán hàng...")
    
    # Khởi tạo database
    print("📊 Đang khởi tạo database...")
    init_db()
    print("✅ Database đã được khởi tạo thành công!")
    
    # Tạo dữ liệu mẫu
    create_sample_data()
    
    print("\n🎯 Hệ thống đã sẵn sàng!")
    print("📝 Để chạy ứng dụng, sử dụng lệnh:")
    print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n🌐 Truy cập: http://localhost:8000")

if __name__ == "__main__":
    main() 