from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ── Discord OAuth ──
class DiscordAuthRequest(BaseModel):
    code: str
    redirect_uri: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    balance: float
    vip_level: int
    xp: int
    total_bet: float
    total_win: float
    refund: float
    created_at: datetime
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserResponse

# ── Game Results ──
class BaccaratResultRequest(BaseModel):
    bet: float
    payout: float
    result: str  # 'player', 'banker', 'tie'
    bet_player: float = 0
    bet_banker: float = 0
    bet_tie: float = 0

class BaccaratResultResponse(BaseModel):
    success: bool
    new_balance: float
    profit: float
    message: str

# ── Leaderboard ──
class LeaderboardEntry(BaseModel):
    rank: int
    id: str
    username: str
    vip_level: int
    balance: float
    total_win: float
    
    class Config:
        from_attributes = True

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_players: int
    current_user_rank: Optional[int] = None

# ── Game History ──
class GameHistoryEntry(BaseModel):
    id: int
    game_type: str
    bet_amount: float
    payout_amount: float
    profit: float
    result: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class GameHistoryResponse(BaseModel):
    games: List[GameHistoryEntry]
    total_bet: float
    total_win: float
    win_rate: float

# ── Notifications ──
class NotificationRequest(BaseModel):
    message: str
    type: str = "info"  # 'info', 'warning', 'error', 'success'
    duration: int = 3000  # milliseconds

# ── Claim Rewards ──
class ClaimHoantrasRequest(BaseModel):
    pass

class ClaimHoantrasResponse(BaseModel):
    success: bool
    amount: float
    new_balance: float
    message: str

# ── Chat ──
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200)

class ChatMessageResponse(BaseModel):
    user_id: str
    username: str
    avatar: Optional[str] = None
    vip_level: int
    message: str
    timestamp: datetime

# ── Error Response ──
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[int] = None
