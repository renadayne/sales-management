from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

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