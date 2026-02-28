# Blueprint: Smart Pharma AI Standalone Service (FEFO & Expiry Alert)

## 1. Tổng quan (Overview)
- **Mục tiêu:** Xây dựng một microservice độc lập bằng Python để xử lý logic thông minh cho kho dược phẩm.
- **Tính năng chính:** - Quản lý logic FEFO (Hết hạn trước - Xuất trước).
    - Cảnh báo các lô hàng sắp hết hạn (Expiry Alerts).
- **Công nghệ:** FastAPI (Python), SQLAlchemy (ORM), PostgreSQL, Pydantic.

## 2. Cấu trúc thư mục (Project Structure)
/smart-pharma-ai
├── main.py              # Entry point & CORS configuration
├── .env                 # Database URL & Settings
├── requirements.txt     # Dependencies
├── app/
│   ├── db/
│   │   ├── session.py   # Database connection logic
│   │   └── models.py    # SQLAlchemy models (Product, Batch)
│   ├── schemas/
│   │   └── schema.py    # Pydantic models for API response
│   ├── services/
│   │   └── fefo_engine.py # Core FEFO & Expiry logic
│   └── api/
│       └── endpoints.py # REST API routes

## 3. Thực thể dữ liệu (Database Schema)
- **Product:** id, name, sku, category.
- **Batch:** id, product_id, batch_code, expiry_date, quantity, status (ACTIVE/EXPIRED).

## 4. Logic nghiệp vụ (Core Business Logic)
### A. Logic FEFO (First Expired, First Out)
- **Input:** `product_id`.
- **Quy trình:**
    1. Truy vấn tất cả các lô hàng (Batches) của sản phẩm.
    2. Lọc bỏ các lô có `quantity == 0` hoặc `expiry_date < today`.
    3. Sắp xếp theo `expiry_date` tăng dần (Hạn gần nhất lên đầu).
    4. Gán nhãn `priority_level`: 
        - CRITICAL: Hạn dưới 15 ngày.
        - WARNING: Hạn từ 15 - 45 ngày.
        - SAFE: Trên 45 ngày.

### B. Cảnh báo hết hạn (Expiry Alerts)
- Quét toàn bộ bảng `Batch`.
- Trả về danh sách các lô hàng có `expiry_date` trong vòng 30 ngày tới.

## 5. Danh sách API (API Endpoints)
- `GET /ai/expiry-alerts`: Trả về danh sách lô hàng sắp hết hạn trên toàn hệ thống.
- `GET /ai/fefo-strategy/{product_id}`: Trả về danh sách lô hàng ưu tiên xuất cho một sản phẩm cụ thể.

## 6. Cấu hình kỹ thuật
- Cho phép CORS từ: `http://localhost:5173` (Frontend Vite).
- Trả về dữ liệu định dạng JSON chuẩn.