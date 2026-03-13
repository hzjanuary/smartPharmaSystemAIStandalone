# Smart Pharma FEFO Service

Backend standalone (FastAPI) cho Smart Pharma System, tối ưu nhẹ để chạy trên TV Box Armbian (1GB RAM).

Service này chỉ xử lý nghiệp vụ FEFO và cảnh báo hết hạn, còn MySQL chạy bên ngoài (Laptop demo).

## Mục tiêu

- FEFO theo lô hàng trong bảng `history_import`.
- Cảnh báo lô sắp hết hạn trong 30 ngày.
- Kết nối MySQL linh hoạt qua biến môi trường `DATABASE_URL`.
- Mở CORS `*` để frontend trên laptop gọi API vào box.

## Tech Stack

- Python 3.10
- FastAPI
- SQLAlchemy 2.x
- PyMySQL
- Docker (`python:3.10-alpine`)

## Cấu trúc hiện tại

```text
.
├── main.py            # FastAPI app + endpoints + CORS
├── database.py        # SQLAlchemy engine/session
├── models.py          # Reflect bảng thực tế từ MySQL
├── logic.py           # FEFO + expiry alert queries
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Database dùng trong logic

Service phản chiếu (reflection) các bảng thực tế:

- `history_import`
- `product`
- `product_category`
- `product_image`
- `supplier`
- `user`

Nghiệp vụ FEFO/alerts hiện tại dùng trực tiếp `history_import` và join `product`.

## Cấu hình môi trường

Tạo file `.env`:

```env
DATABASE_URL=mysql+pymysql://root:password@10.0.8.100:3306/smart_pharma
```

Bạn có thể đổi IP/credentials tùy môi trường mà không cần sửa code.

## Chạy local (không Docker)

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Chạy bằng Docker

```bash
docker compose up --build -d
```

`docker-compose.yml` chỉ chạy duy nhất service backend, không khởi chạy database container.

## API Endpoints

| Method | Endpoint | Mô tả |
| ------ | -------- | ----- |
| GET | `/` | Thông tin service |
| GET | `/fefo/{product_id}` | Danh sách lô của sản phẩm, sắp xếp `expiry_date` tăng dần, chỉ lấy `quantity > 0` |
| GET | `/alerts/expiry` | Danh sách lô hết hạn trong 30 ngày tới |

## Ví dụ response

### `GET /fefo/1`

```json
{
	"product_id": 1,
	"total_batches": 2,
	"batches": [
		{
			"history_id": 10,
			"product_id": 1,
			"product_name": "Paracetamol 500mg",
			"batch_code": "LOT-2026-01",
			"quantity": 120,
			"expiry_date": "2026-05-01"
		}
	]
}
```

### `GET /alerts/expiry`

```json
{
	"window_days": 30,
	"total_alerts": 1,
	"alerts": [
		{
			"history_id": 10,
			"product_id": 1,
			"product_name": "Paracetamol 500mg",
			"batch_code": "LOT-2026-01",
			"quantity": 120,
			"expiry_date": "2026-04-10",
			"days_to_expiry": 28
		}
	]
}
```

## CORS

Đã bật:

```python
allow_origins=["*"]
```

Phù hợp cho môi trường demo LAN giữa TV Box và laptop.
