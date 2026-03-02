# Smart Pharma AI Service

Microservice độc lập xử lý logic AI cho hệ thống quản lý kho dược phẩm.

## Tính năng

- **FEFO Strategy** (First Expired, First Out): Ưu tiên xuất hàng sắp hết hạn trước
- **Expiry Alerts**: Cảnh báo các lô hàng sắp hết hạn trong hệ thống
- **Priority Classification**: Tự động phân loại mức độ ưu tiên (CRITICAL/WARNING/SAFE)

## Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Validation**: Pydantic v2

## Cấu trúc dự án

```
smart-pharma-ai/
├── main.py                 # Entry point & CORS config
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── app/
│   ├── db/
│   │   ├── session.py      # Database connection
│   │   └── models.py       # SQLAlchemy models
│   ├── schemas/
│   │   └── schema.py       # Pydantic schemas
│   ├── services/
│   │   └── fefo_engine.py  # Core FEFO logic
│   └── api/
│       └── endpoints.py    # REST API routes
```

## Cài đặt

```bash
# Clone repository
git clone <repository-url>
cd smartPharmaSystemAIFeatures

# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình environment
cp .env.example .env
# Chỉnh sửa .env theo nhu cầu
```

## Chạy ứng dụng

```bash
# Development (auto-reload)
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

| Method | Endpoint                                | Mô tả                                    |
| ------ | --------------------------------------- | ---------------------------------------- |
| GET    | `/`                                     | Thông tin service                        |
| GET    | `/ai/health`                            | Health check                             |
| GET    | `/ai/fefo-strategy/{product_id}`        | Danh sách lô hàng ưu tiên xuất theo FEFO |
| GET    | `/ai/expiry-alerts`                     | Danh sách lô hàng sắp hết hạn            |
| POST   | `/ai/maintenance/update-expired-status` | Cập nhật status batch đã hết hạn         |

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Logic FEFO

### Priority Levels

| Level    | Ngày còn lại | Hành động         |
| -------- | ------------ | ----------------- |
| CRITICAL | < 15 ngày    | Xuất ngay lập tức |
| WARNING  | 15-45 ngày   | Ưu tiên xuất      |
| SAFE     | > 45 ngày    | Xử lý bình thường |

### Quy trình FEFO

1. Truy vấn tất cả lô hàng của sản phẩm
2. Lọc bỏ lô có `quantity = 0` hoặc đã hết hạn
3. Sắp xếp theo `expiry_date` tăng dần
4. Gán `priority_level` dựa trên số ngày còn lại

## CORS Configuration

Cho phép request từ:

- `http://localhost:5173` (Vite/React)
- `http://localhost:3000` (Create React App)

## Environment Variables

| Variable     | Mô tả                                | Default                     |
| ------------ | ------------------------------------ | --------------------------- |
| DATABASE_URL | Database connection string           | sqlite:///./smart_pharma.db |
| APP_ENV      | Environment (development/production) | development                 |
| DEBUG        | Enable debug mode                    | true                        |
