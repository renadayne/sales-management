from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import init_db
from app.routes import product

# Khởi tạo FastAPI app
app = FastAPI(
    title="Hệ thống Quản lý Bán hàng",
    description="Hệ thống quản lý sản phẩm và kho hàng nội bộ",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo thư mục static nếu chưa có
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(product.router, prefix="/products", tags=["products"])

@app.get("/")
async def root():
    """Trang chủ - chuyển hướng đến danh sách sản phẩm"""
    return {"message": "Hệ thống Quản lý Bán hàng", "redirect": "/products"}

@app.on_event("startup")
async def startup_event():
    """Khởi tạo database khi ứng dụng khởi động"""
    init_db()
    print("✅ Database đã được khởi tạo thành công!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 