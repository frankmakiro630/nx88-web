# NX88 Casino - Backend API

FastAPI + PostgreSQL backend cho casino game trực tuyến.

## 📋 Tính năng

- ✅ Discord OAuth 2.0 authentication
- ✅ Baccarat game API (result logging, history, stats)
- ✅ Slot machine API
- ✅ User profiles & VIP system
- ✅ Leaderboards (balance & VIP)
- ✅ Balance & transaction management
- ✅ Game history tracking

## 🚀 Quick Start

### 1. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database (Docker)

```bash
# Khởi động PostgreSQL và Redis
docker-compose up -d

# Xem logs (optional)
docker-compose logs -f
```

Hoặc tạo database thủ công:
```sql
CREATE DATABASE nx88_casino;
CREATE USER nx88_user WITH PASSWORD 'nx88_password_123';
GRANT ALL PRIVILEGES ON DATABASE nx88_casino TO nx88_user;
```

### 3. Cấu hình Environment

Copy `.env.example` thành `.env`:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
# Discord OAuth (lấy từ https://discord.com/developers/applications)
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_secret_here
DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback

# Database
DATABASE_URL=postgresql://nx88_user:nx88_password_123@localhost:5432/nx88_casino

# Server
DEBUG=True
PORT=8000
```

### 4. Chạy Server

```bash
python main.py
```

hoặc

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs** (Swagger UI)

## 📚 API Endpoints

### Authentication

#### POST `/api/auth/discord`
Exchange Discord OAuth code for JWT token
```bash
curl -X POST http://localhost:8000/api/auth/discord \
  -H "Content-Type: application/json" \
  -d '{
    "code": "oauth_code_from_discord",
    "redirect_uri": "http://localhost:3000/auth/discord/callback"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "123456",
    "username": "player_name",
    "balance": 1000000,
    "vip_level": 0,
    "xp": 0
  }
}
```

### User

#### GET `/api/user/profile`
Get current user profile
```bash
curl -X GET http://localhost:8000/api/user/profile \
  -H "Authorization: Bearer {token}"
```

#### POST `/api/user/claim-hoantra`
Claim VIP refund bonus
```bash
curl -X POST http://localhost:8000/api/user/claim-hoantra \
  -H "Authorization: Bearer {token}"
```

### Baccarat

#### POST `/api/baccarat/result`
Log baccarat game result
```bash
curl -X POST http://localhost:8000/api/baccarat/result \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "bet": 100000,
    "payout": 190000,
    "result": "player",
    "bet_player": 100000,
    "bet_banker": 0,
    "bet_tie": 0
  }'
```

#### GET `/api/baccarat/history`
Get game history
```bash
curl -X GET http://localhost:8000/api/baccarat/history?limit=50 \
  -H "Authorization: Bearer {token}"
```

#### GET `/api/baccarat/stats`
Get game statistics
```bash
curl -X GET http://localhost:8000/api/baccarat/stats \
  -H "Authorization: Bearer {token}"
```

### Leaderboard

#### GET `/api/leaderboard`
Get leaderboard
```bash
# By balance
curl -X GET "http://localhost:8000/api/leaderboard?mode=balance&limit=100" \
  -H "Authorization: Bearer {token}"

# By VIP level
curl -X GET "http://localhost:8000/api/leaderboard?mode=vip&limit=100" \
  -H "Authorization: Bearer {token}"
```

### Slot Machine

#### POST `/api/slot/spin`
Spin slot machine
```bash
curl -X POST http://localhost:8000/api/slot/spin \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"bet": 50000}'
```

## 🗄️ Database Schema

### Users
- id (Discord ID)
- username
- email
- balance
- vip_level (0-5)
- xp
- total_bet
- total_win
- refund
- is_admin
- is_banned

### GameHistory
- game_type (slot, baccarat, xocdia)
- bet_amount
- payout_amount
- result
- created_at

### Transactions
- type (deposit, withdraw, win, loss, refund)
- amount
- status
- created_at

## 🔐 Authentication

Token được lưu trong **localStorage** trên client:
```json
{
  "token": "jwt_token",
  "user": {...}
}
```

Header yêu cầu:
```
Authorization: Bearer {token}
```

Token hết hạn sau **7 ngày** (có thể chỉnh trong `config.py`)

## 🎮 Game Logic

### Baccarat Payout
- **Player thắng**: gốc × 1.95 (ít hơn 2 do commission)
- **Banker thắng**: gốc × 1.95 (5% commission)
- **Tie thắng**: gốc × 8.0
- **Thua**: mất gốc

### VIP System
| Level | Tiêu đề | Hoàn trả | XP Cần |
|-------|---------|---------|-------|
| 0 | TÂN THỦ | 2% | 0 |
| 1 | ÔNG CHỦ | 5% | 10k |
| 2 | THIẾU GIA | 8% | 50k |
| 3 | ĐẾ VƯƠNG | 12% | 100k |
| 4 | HOÀNG ĐẾ | 15% | 250k |
| 5 | THẦN TÀI | 20% | 500k |

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres

# Access PostgreSQL shell
docker exec -it nx88_postgres psql -U nx88_user -d nx88_casino
```

## 📝 Logging & Debug

Enable debug mode in `.env`:
```env
DEBUG=True
```

Check server logs:
```bash
tail -f /var/log/nx88/api.log
```

## 🔗 Connect Frontend

Frontend đã được cấu hình tại `index.html` để kết nối với:
- API Base: `http://localhost:8000`
- Discord Callback: `http://localhost:3000/auth/discord/callback`

## 🛠️ Troubleshooting

### "Database connection failed"
```bash
# Kiểm tra PostgreSQL running
docker ps | grep postgres

# Kiểm tra connection string trong .env
DATABASE_URL=postgresql://user:pass@localhost:5432/nx88_casino
```

### "Discord OAuth error"
1. Kiểm tra CLIENT_ID và CLIENT_SECRET đúng
2. Kiểm tra REDIRECT_URI match trong Discord dev portal
3. Kiểm tra scopes: `identify email`

### "Token expired"
Frontend sẽ tự động gọi `/api/auth/discord` lại khi token hết hạn

## 📞 Support

Mở terminal và chạy:
```bash
python main.py --debug
```

Truy cập: `http://localhost:8000/docs` để test API trực tiếp
