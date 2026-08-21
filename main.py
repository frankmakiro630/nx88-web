from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Optional, List
import httpx
import jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local modules
from config import settings
from models import Base, User, GameHistory, Transaction, OAuthToken, BaccaratRound
from schemas import (
    DiscordAuthRequest, AuthResponse, UserResponse,
    BaccaratResultRequest, BaccaratResultResponse,
    LeaderboardEntry, LeaderboardResponse,
    ErrorResponse, ClaimHoantrasResponse
)

# ════════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ════════════════════════════════════════════════════════════════════════════

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="NX88 Casino Backend API"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════════════════════════════════════════

def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = {"sub": user_id, "type": "access"}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.InvalidTokenError:
        return None

def get_current_user(token: str, db: Session) -> User:
    """Get current user from token"""
    if token.startswith("Bearer "):
        token = token[7:]
    
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# ════════════════════════════════════════════════════════════════════════════
# DISCORD OAUTH ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/discord", response_model=AuthResponse)
async def discord_auth(request: DiscordAuthRequest, db: Session = Depends(get_db)):
    """
    Exchange Discord OAuth code for access token
    """
    try:
        # Exchange code for Discord token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{settings.DISCORD_API_URL}/oauth2/token",
                data={
                    "client_id": settings.DISCORD_CLIENT_ID,
                    "client_secret": settings.DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": request.code,
                    "redirect_uri": request.redirect_uri,
                    "scope": "identify email"
                }
            )
            
            if token_response.status_code != 200:
                raise Exception("Failed to get Discord token")
            
            discord_token = token_response.json()
            access_token = discord_token.get("access_token")
            
            # Get Discord user info
            user_response = await client.get(
                f"{settings.DISCORD_API_URL}/users/@me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise Exception("Failed to get Discord user info")
            
            discord_user = user_response.json()
            user_id = discord_user.get("id")
            username = discord_user.get("username")
            email = discord_user.get("email")
            avatar = discord_user.get("avatar")
        
        # Find or create user in database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            # Create new user
            user = User(
                id=user_id,
                username=username,
                email=email,
                avatar=avatar,
                balance=1000000.0,  # Starting balance
                vip_level=0,
                xp=0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            # Update avatar if changed
            if avatar and user.avatar != avatar:
                user.avatar = avatar
            db.commit()
        
        # Create JWT token
        jwt_token = create_access_token(user_id)
        
        return AuthResponse(
            token=jwt_token,
            user=UserResponse.from_orm(user)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )

# ════════════════════════════════════════════════════════════════════════════
# USER ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/user/profile", response_model=UserResponse)
async def get_profile(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    user = get_current_user(authorization, db)
    return UserResponse.from_orm(user)

@app.post("/api/user/claim-hoantra", response_model=ClaimHoantrasResponse)
async def claim_hoantra(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Claim VIP refund bonus"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    user = get_current_user(authorization, db)
    
    # Calculate hoantra based on VIP level and recent bets
    # Example: VIP 1 = 2%, VIP 2 = 5%, etc.
    vip_rates = [0.02, 0.05, 0.08, 0.12, 0.15, 0.20]
    rate = vip_rates[min(user.vip_level, len(vip_rates) - 1)]
    
    # Get total bet in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_games = db.query(GameHistory).filter(
        GameHistory.user_id == user.id,
        GameHistory.created_at >= yesterday
    ).all()
    
    total_bet_24h = sum(g.bet_amount for g in recent_games)
    hoantra_amount = int(total_bet_24h * rate)
    
    if hoantra_amount <= 0:
        return ClaimHoantrasResponse(
            success=False,
            amount=0,
            new_balance=user.balance,
            message="No refund available"
        )
    
    # Add to balance
    user.balance += hoantra_amount
    
    # Record transaction
    transaction = Transaction(
        user_id=user.id,
        type="refund",
        amount=hoantra_amount,
        balance_before=user.balance - hoantra_amount,
        balance_after=user.balance,
        description=f"VIP {user.vip_level} Hoantra ({rate*100}%)"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(user)
    
    return ClaimHoantrasResponse(
        success=True,
        amount=hoantra_amount,
        new_balance=user.balance,
        message=f"Claimed {hoantra_amount} hoantra"
    )

# ════════════════════════════════════════════════════════════════════════════
# BACCARAT ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/baccarat/result", response_model=BaccaratResultResponse)
async def baccarat_result(
    request: BaccaratResultRequest,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Log baccarat game result and update balance"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    user = get_current_user(authorization, db)
    
    # Validate request
    if request.bet <= 0 or request.payout < 0:
        raise HTTPException(status_code=400, detail="Invalid bet or payout")
    
    profit = request.payout - request.bet
    
    # Update user balance
    user.balance += profit
    user.total_bet += request.bet
    if request.payout > 0:
        user.total_win += request.payout
    
    # Add XP for VIP progression
    xp_gain = int(request.bet / 100000)  # 1 XP per 100k bet
    user.xp += xp_gain
    
    # Check VIP level up
    xp_thresholds = [0, 10000, 50000, 100000, 250000, 500000]
    for level, threshold in enumerate(xp_thresholds):
        if user.xp >= threshold:
            user.vip_level = level
    
    # Record game history
    game = GameHistory(
        user_id=user.id,
        game_type="baccarat",
        bet_amount=request.bet,
        payout_amount=request.payout,
        profit=profit,
        result=request.result,
        bet_player=request.bet_player,
        bet_banker=request.bet_banker,
        bet_tie=request.bet_tie
    )
    
    db.add(game)
    db.commit()
    db.refresh(user)
    
    return BaccaratResultResponse(
        success=True,
        new_balance=user.balance,
        profit=profit,
        message=f"Game recorded - {request.result} wins"
    )

@app.get("/api/baccarat/history")
async def baccarat_history(
    authorization: str = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get user's baccarat game history"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    user = get_current_user(authorization, db)
    
    games = db.query(GameHistory).filter(
        GameHistory.user_id == user.id,
        GameHistory.game_type == "baccarat"
    ).order_by(desc(GameHistory.created_at)).limit(limit).all()
    
    return [
        {
            "id": g.id,
            "result": g.result,
            "bet": g.bet_amount,
            "payout": g.payout_amount,
            "profit": g.profit,
            "player_score": g.player_score,
            "banker_score": g.banker_score,
            "created_at": g.created_at
        }
        for g in games
    ]

@app.get("/api/baccarat/stats")
async def baccarat_stats(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Get user's baccarat statistics"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    user = get_current_user(authorization, db)
    
    games = db.query(GameHistory).filter(
        GameHistory.user_id == user.id,
        GameHistory.game_type == "baccarat"
    ).all()
    
    total_games = len(games)
    total_bet = sum(g.bet_amount for g in games)
    total_win = sum(g.payout_amount for g in games)
    total_profit = sum(g.profit for g in games)
    
    results = {
        "player": sum(1 for g in games if g.result == "player"),
        "banker": sum(1 for g in games if g.result == "banker"),
        "tie": sum(1 for g in games if g.result == "tie")
    }
    
    return {
        "total_games": total_games,
        "total_bet": total_bet,
        "total_win": total_win,
        "total_profit": total_profit,
        "win_rate": (total_games - results["banker"] - results["tie"]) / max(1, total_games) * 100 if total_games > 0 else 0,
        "results": results
    }

# ════════════════════════════════════════════════════════════════════════════
# LEADERBOARD ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/api/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    mode: str = Query("balance", regex="^(balance|vip)$"),
    limit: int = Query(100, le=200),
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get leaderboard (balance or VIP)"""
    
    current_user_id = None
    current_user_rank = None
    
    if authorization:
        try:
            current_user_id = verify_token(authorization.replace("Bearer ", ""))
        except:
            pass
    
    if mode == "balance":
        # Sort by balance
        users = db.query(User).filter(
            User.is_banned == False
        ).order_by(desc(User.balance)).limit(limit).all()
    else:  # vip
        # Sort by VIP level, then XP
        users = db.query(User).filter(
            User.is_banned == False
        ).order_by(desc(User.vip_level), desc(User.xp)).limit(limit).all()
    
    entries = []
    for rank, user in enumerate(users, 1):
        if user.id == current_user_id:
            current_user_rank = rank
        
        entry = LeaderboardEntry(
            rank=rank,
            id=user.id,
            username=user.username,
            vip_level=user.vip_level,
            balance=user.balance,
            total_win=user.total_win
        )
        entries.append(entry)
    
    total_players = db.query(func.count(User.id)).filter(
        User.is_banned == False
    ).scalar()
    
    return LeaderboardResponse(
        entries=entries,
        total_players=total_players,
        current_user_rank=current_user_rank
    )

# ════════════════════════════════════════════════════════════════════════════
# SLOT ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.post("/api/slot/spin")
async def slot_spin(
    bet: float,
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """Log slot spin result"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    user = get_current_user(authorization, db)
    
    if user.balance < bet:
        return {"success": False, "error": "Insufficient balance"}
    
    # Simulate spin result (in production, this would be secure server-side)
    import random
    payout_multipliers = [0, 0, 0, 1, 1.8, 2.5, 4, 10, 25, 80]
    multiplier = random.choice(payout_multipliers)
    payout = int(bet * multiplier)
    profit = payout - bet
    
    # Update user
    user.balance += profit
    user.total_bet += bet
    if payout > 0:
        user.total_win += payout
    
    # Record game
    game = GameHistory(
        user_id=user.id,
        game_type="slot",
        bet_amount=bet,
        payout_amount=payout,
        profit=profit,
        result="win" if payout > 0 else "loss",
        multiplier=multiplier
    )
    
    db.add(game)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "multiplier": multiplier,
        "payout": payout,
        "profit": profit,
        "new_balance": user.balance
    }

# ════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ════════════════════════════════════════════════════════════════════════════

@app.get("/auth/discord/callback")
async def discord_callback():
    """OAuth callback route - serve index.html so frontend can handle the code parameter"""
    try:
        return FileResponse(
            os.path.join(os.path.dirname(__file__), "index.html"),
            media_type="text/html"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Could not load index.html", "details": str(e)}
        )

@app.get("/")
async def root():
    """Health check"""
    return {"status": "online", "version": "1.0.0", "app": "NX88 Casino API"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
