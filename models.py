from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)  # Discord user ID
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    avatar = Column(String(500))
    
    # Balance & Transactions
    balance = Column(Float, default=0)
    total_bet = Column(Float, default=0)
    total_win = Column(Float, default=0)
    refund = Column(Float, default=0)
    
    # VIP System
    vip_level = Column(Integer, default=0)  # 0-5: TÂN THỦ, ÔNG CHỦ, THIẾU GIA, ĐẾ VƯƠNG, HOÀNG ĐẾ, THẦN TÀI
    xp = Column(Integer, default=0)
    
    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # Relationships
    game_history = relationship("GameHistory", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


class GameHistory(Base):
    __tablename__ = "game_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    game_type = Column(String(50), nullable=False)  # 'slot', 'baccarat', 'xocdia', etc
    
    # Game Details
    bet_amount = Column(Float, nullable=False)
    payout_amount = Column(Float, nullable=False)
    profit = Column(Float)  # payout - bet
    result = Column(String(50))  # 'win', 'loss', 'draw', 'player', 'banker', 'tie'
    
    # Baccarat specific
    bet_player = Column(Float, default=0)
    bet_banker = Column(Float, default=0)
    bet_tie = Column(Float, default=0)
    player_score = Column(Integer)
    banker_score = Column(Integer)
    
    # Slot specific
    reel_result = Column(String(100))
    multiplier = Column(Float, default=1.0)
    
    game_data = Column(JSON)  # Store full game state if needed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="game_history")
    
    def __repr__(self):
        return f"<GameHistory {self.game_type} {self.id}>"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    
    type = Column(String(50), nullable=False)  # 'deposit', 'withdraw', 'win', 'loss', 'refund'
    amount = Column(Float, nullable=False)
    balance_before = Column(Float)
    balance_after = Column(Float)
    
    description = Column(String(255))
    status = Column(String(20), default="completed")  # 'pending', 'completed', 'failed'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.type} {self.amount}>"


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500))
    token_type = Column(String(50), default="Bearer")
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OAuthToken {self.user_id}>"


class BaccaratRound(Base):
    __tablename__ = "baccarat_rounds"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    round_number = Column(Integer)
    result = Column(String(20), nullable=False)  # 'player', 'banker', 'tie'
    
    player_cards = Column(String(100))
    player_score = Column(Integer)
    
    banker_cards = Column(String(100))
    banker_score = Column(Integer)
    
    total_pool = Column(Float, default=0)
    player_pool = Column(Float, default=0)
    banker_pool = Column(Float, default=0)
    tie_pool = Column(Float, default=0)
    
    shoe_remaining = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BaccaratRound {self.round_number} {self.result}>"
