# 05. Database Migration và Backup

## Tổng quan

Migration và backup là các hoạt động quan trọng để đảm bảo tính toàn vẹn và khả năng phục hồi dữ liệu. Tài liệu này hướng dẫn cách thực hiện migration và backup cho hệ thống SQLite.

## 1. Database Migration

### 1.1 Manual Migration

#### Tạo migration script
```python
# migrations/001_add_user_table.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from sqlalchemy import text

def migrate_001_add_user_table():
    """Migration: Thêm bảng users"""
    with engine.connect() as conn:
        # Tạo bảng users
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Tạo index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
        """))
        
        conn.commit()
        print("✅ Migration 001: Thêm bảng users thành công")

def rollback_001_add_user_table():
    """Rollback migration 001"""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.commit()
        print("✅ Rollback 001: Xóa bảng users thành công")
```

#### Migration manager
```python
# migrations/migration_manager.py
import os
import sys
from datetime import datetime
from typing import List, Dict

class MigrationManager:
    def __init__(self):
        self.migrations: List[Dict] = [
            {
                "id": "001",
                "name": "add_user_table",
                "function": "migrate_001_add_user_table",
                "rollback": "rollback_001_add_user_table",
                "applied": False
            },
            {
                "id": "002", 
                "name": "add_product_status",
                "function": "migrate_002_add_product_status",
                "rollback": "rollback_002_add_product_status",
                "applied": False
            }
        ]
    
    def create_migration_table(self):
        """Tạo bảng theo dõi migrations"""
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Lấy danh sách migrations đã apply"""
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT id FROM migrations ORDER BY id"))
            return [row[0] for row in result]
        finally:
            db.close()
    
    def apply_migration(self, migration_id: str):
        """Apply một migration"""
        migration = next((m for m in self.migrations if m["id"] == migration_id), None)
        if not migration:
            raise ValueError(f"Migration {migration_id} không tồn tại")
        
        # Import và thực hiện migration
        import importlib
        migration_module = importlib.import_module(f"migrations.{migration_id}_{migration['name']}")
        
        migration_func = getattr(migration_module, migration["function"])
        migration_func()
        
        # Ghi lại migration đã apply
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("""
                INSERT INTO migrations (id, name) VALUES (:id, :name)
            """), {"id": migration_id, "name": migration["name"]})
            db.commit()
        finally:
            db.close()
        
        print(f"✅ Migration {migration_id} đã được apply")
    
    def apply_all_migrations(self):
        """Apply tất cả migrations chưa được apply"""
        self.create_migration_table()
        applied_migrations = self.get_applied_migrations()
        
        for migration in self.migrations:
            if migration["id"] not in applied_migrations:
                print(f"🔄 Applying migration {migration['id']}: {migration['name']}")
                self.apply_migration(migration["id"])
    
    def rollback_migration(self, migration_id: str):
        """Rollback một migration"""
        migration = next((m for m in self.migrations if m["id"] == migration_id), None)
        if not migration:
            raise ValueError(f"Migration {migration_id} không tồn tại")
        
        # Import và thực hiện rollback
        import importlib
        migration_module = importlib.import_module(f"migrations.{migration_id}_{migration['name']}")
        
        rollback_func = getattr(migration_module, migration["rollback"])
        rollback_func()
        
        # Xóa migration khỏi bảng applied
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM migrations WHERE id = :id"), {"id": migration_id})
            db.commit()
        finally:
            db.close()
        
        print(f"✅ Migration {migration_id} đã được rollback")

# Sử dụng
if __name__ == "__main__":
    manager = MigrationManager()
    manager.apply_all_migrations()
```

### 1.2 Alembic Migration (Advanced)

#### Cài đặt Alembic
```bash
pip install alembic
```

#### Khởi tạo Alembic
```bash
alembic init alembic
```

#### Cấu hình Alembic
```python
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///./data/sales_management.db
```

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### Tạo migration với Alembic
```bash
# Tạo migration mới
alembic revision --autogenerate -m "add user table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 2. Database Backup

### 2.1 Manual Backup

#### Backup script
```python
# scripts/backup_database.py
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

class DatabaseBackup:
    def __init__(self, db_path: str = "./data/sales_management.db"):
        self.db_path = db_path
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, include_images: bool = True) -> str:
        """Tạo backup database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"sales_management_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.db"
        
        # Copy database file
        shutil.copy2(self.db_path, backup_path)
        
        # Backup images nếu cần
        if include_images:
            images_backup_path = self.backup_dir / f"{backup_name}_images.zip"
            self._backup_images(images_backup_path)
        
        print(f"✅ Backup created: {backup_path}")
        return str(backup_path)
    
    def _backup_images(self, backup_path: Path):
        """Backup thư mục images"""
        images_dir = Path("./static/uploads")
        if images_dir.exists():
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in images_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(images_dir)
                        zipf.write(file_path, arcname)
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database từ backup"""
        if not os.path.exists(backup_path):
            print(f"❌ Backup file không tồn tại: {backup_path}")
            return False
        
        try:
            # Stop application (nếu cần)
            # self._stop_application()
            
            # Restore database
            shutil.copy2(backup_path, self.db_path)
            
            # Restore images nếu có
            images_backup = backup_path.replace('.db', '_images.zip')
            if os.path.exists(images_backup):
                self._restore_images(images_backup)
            
            print(f"✅ Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi restore: {e}")
            return False
    
    def _restore_images(self, images_backup_path: str):
        """Restore images từ backup"""
        images_dir = Path("./static/uploads")
        images_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(images_backup_path, 'r') as zipf:
            zipf.extractall(images_dir)
    
    def list_backups(self) -> list:
        """Liệt kê tất cả backups"""
        backups = []
        for file_path in self.backup_dir.glob("sales_management_*.db"):
            stat = file_path.stat()
            backups.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime),
                "path": str(file_path)
            })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Xóa backups cũ"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup in self.list_backups():
            if backup["created_at"] < cutoff_date:
                os.remove(backup["path"])
                
                # Xóa file images backup tương ứng
                images_backup = backup["path"].replace('.db', '_images.zip')
                if os.path.exists(images_backup):
                    os.remove(images_backup)
                
                print(f"🗑️ Deleted old backup: {backup['filename']}")

# Sử dụng
if __name__ == "__main__":
    backup_manager = DatabaseBackup()
    
    # Tạo backup
    backup_path = backup_manager.create_backup()
    
    # Liệt kê backups
    backups = backup_manager.list_backups()
    for backup in backups:
        print(f"📁 {backup['filename']} - {backup['size']} bytes - {backup['created_at']}")
    
    # Cleanup old backups
    backup_manager.cleanup_old_backups(keep_days=7)
```

### 2.2 Automated Backup

#### Cron job script
```python
# scripts/auto_backup.py
import schedule
import time
from backup_database import DatabaseBackup

def daily_backup():
    """Backup hàng ngày"""
    backup_manager = DatabaseBackup()
    backup_path = backup_manager.create_backup()
    print(f"📅 Daily backup completed: {backup_path}")

def weekly_backup():
    """Backup hàng tuần với cleanup"""
    backup_manager = DatabaseBackup()
    backup_path = backup_manager.create_backup()
    backup_manager.cleanup_old_backups(keep_days=30)
    print(f"📅 Weekly backup completed: {backup_path}")

# Lập lịch backup
schedule.every().day.at("02:00").do(daily_backup)
schedule.every().sunday.at("03:00").do(weekly_backup)

if __name__ == "__main__":
    print("🔄 Auto backup service started...")
    while True:
        schedule.run_pending()
        time.sleep(60)
```

#### Systemd service (Linux)
```ini
# /etc/systemd/system/sales-backup.service
[Unit]
Description=Sales Management Database Backup
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/sales-management
ExecStart=/usr/bin/python3 scripts/auto_backup.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2.3 Backup Verification

#### Verify backup integrity
```python
def verify_backup(backup_path: str) -> bool:
    """Kiểm tra tính toàn vẹn của backup"""
    import sqlite3
    
    try:
        # Kết nối database backup
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Kiểm tra cấu trúc bảng
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['products', 'product_logs']
        for table in required_tables:
            if table not in tables:
                print(f"❌ Missing table: {table}")
                return False
        
        # Kiểm tra dữ liệu
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_logs")
        log_count = cursor.fetchone()[0]
        
        print(f"✅ Backup verification passed:")
        print(f"   - Tables: {len(tables)}")
        print(f"   - Products: {product_count}")
        print(f"   - Logs: {log_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Backup verification failed: {e}")
        return False
```

## 3. Data Export/Import

### 3.1 Export Data

#### Export to JSON
```python
import json
from datetime import datetime

def export_to_json(db: Session, export_path: str = None):
    """Export database ra JSON"""
    if not export_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"exports/data_export_{timestamp}.json"
    
    # Tạo thư mục exports nếu chưa có
    os.makedirs("exports", exist_ok=True)
    
    # Lấy dữ liệu
    products = db.query(Product).all()
    logs = db.query(ProductLog).all()
    
    # Chuyển đổi thành dict
    data = {
        "exported_at": datetime.now().isoformat(),
        "products": [product.to_dict() for product in products],
        "logs": [log.to_dict() for log in logs]
    }
    
    # Ghi file
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Data exported to: {export_path}")
    return export_path
```

#### Export to CSV
```python
import csv

def export_to_csv(db: Session, export_dir: str = "exports"):
    """Export database ra CSV files"""
    os.makedirs(export_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export products
    products = db.query(Product).all()
    products_file = f"{export_dir}/products_{timestamp}.csv"
    
    with open(products_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'sku', 'price', 'quantity', 'category', 'description', 'created_at', 'updated_at'])
        
        for product in products:
            writer.writerow([
                product.id, product.name, product.sku, product.price,
                product.quantity, product.category, product.description,
                product.created_at, product.updated_at
            ])
    
    # Export logs
    logs = db.query(ProductLog).all()
    logs_file = f"{export_dir}/logs_{timestamp}.csv"
    
    with open(logs_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'product_id', 'action', 'field_name', 'old_value', 'new_value', 'changed_by', 'created_at'])
        
        for log in logs:
            writer.writerow([
                log.id, log.product_id, log.action, log.field_name,
                log.old_value, log.new_value, log.changed_by, log.created_at
            ])
    
    print(f"✅ Data exported to CSV:")
    print(f"   - Products: {products_file}")
    print(f"   - Logs: {logs_file}")
    
    return [products_file, logs_file]
```

### 3.2 Import Data

#### Import from JSON
```python
def import_from_json(db: Session, import_path: str):
    """Import dữ liệu từ JSON"""
    with open(import_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Import products
    for product_data in data.get('products', []):
        # Bỏ qua ID để tránh conflict
        product_data.pop('id', None)
        product = Product(**product_data)
        db.add(product)
    
    # Import logs
    for log_data in data.get('logs', []):
        log_data.pop('id', None)
        log = ProductLog(**log_data)
        db.add(log)
    
    db.commit()
    print(f"✅ Data imported from: {import_path}")
```

## 4. Database Maintenance

### 4.1 Vacuum Database
```python
def vacuum_database():
    """Tối ưu database"""
    from app.database import engine
    
    with engine.connect() as conn:
        conn.execute(text("VACUUM"))
        conn.commit()
    
    print("✅ Database vacuumed successfully")
```

### 4.2 Analyze Database
```python
def analyze_database():
    """Phân tích database"""
    from app.database import engine
    
    with engine.connect() as conn:
        conn.execute(text("ANALYZE"))
        conn.commit()
    
    print("✅ Database analyzed successfully")
```

### 4.3 Check Database Integrity
```python
def check_database_integrity():
    """Kiểm tra tính toàn vẹn database"""
    from app.database import engine
    
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA integrity_check"))
        integrity_result = result.fetchone()[0]
        
        if integrity_result == "ok":
            print("✅ Database integrity check passed")
            return True
        else:
            print(f"❌ Database integrity check failed: {integrity_result}")
            return False
```

## 5. Disaster Recovery

### 5.1 Recovery Plan
```python
class DisasterRecovery:
    def __init__(self):
        self.backup_manager = DatabaseBackup()
    
    def create_recovery_plan(self):
        """Tạo kế hoạch phục hồi"""
        plan = {
            "backup_frequency": "daily",
            "backup_retention": "30 days",
            "recovery_time_objective": "4 hours",
            "recovery_point_objective": "24 hours",
            "backup_locations": ["local", "cloud"],
            "contact_person": "admin@company.com"
        }
        
        with open("disaster_recovery_plan.json", 'w') as f:
            json.dump(plan, f, indent=2)
        
        return plan
    
    def test_recovery(self, backup_path: str):
        """Test khôi phục từ backup"""
        # Tạo database test
        test_db_path = "./data/test_recovery.db"
        
        # Copy backup vào test database
        shutil.copy2(backup_path, test_db_path)
        
        # Test kết nối và queries
        try:
            from sqlalchemy import create_engine
            test_engine = create_engine(f"sqlite:///{test_db_path}")
            
            with test_engine.connect() as conn:
                # Test basic queries
                result = conn.execute(text("SELECT COUNT(*) FROM products"))
                product_count = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM product_logs"))
                log_count = result.fetchone()[0]
                
                print(f"✅ Recovery test passed:")
                print(f"   - Products: {product_count}")
                print(f"   - Logs: {log_count}")
                
                return True
                
        except Exception as e:
            print(f"❌ Recovery test failed: {e}")
            return False
        finally:
            # Cleanup test database
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
```

### 5.2 Automated Recovery
```python
def automated_recovery():
    """Tự động phục hồi khi có sự cố"""
    # Kiểm tra database integrity
    if not check_database_integrity():
        print("🚨 Database corruption detected!")
        
        # Tìm backup gần nhất
        backup_manager = DatabaseBackup()
        backups = backup_manager.list_backups()
        
        if backups:
            latest_backup = backups[0]
            print(f"🔄 Attempting recovery from: {latest_backup['filename']}")
            
            # Restore từ backup
            if backup_manager.restore_backup(latest_backup['path']):
                print("✅ Recovery completed successfully")
                return True
            else:
                print("❌ Recovery failed")
                return False
        else:
            print("❌ No backup available for recovery")
            return False
    else:
        print("✅ Database integrity check passed")
        return True 