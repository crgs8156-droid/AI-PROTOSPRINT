from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
import uuid


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserInDB(User):
    hashed_password: str


class HabitCreate(BaseModel):
    name: str
    emoji: str = "✅"
    color: str = "#10B981"


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    emoji: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class Habit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    emoji: str
    color: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CompletionCreate(BaseModel):
    habit_id: str
    completed_date: Optional[date] = None


class Completion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    habit_id: str
    user_id: str
    completed_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JournalEntryCreate(BaseModel):
    content: str
    mood: str
    entry_date: Optional[date] = None


class JournalEntryUpdate(BaseModel):
    content: Optional[str] = None
    mood: Optional[str] = None


class JournalEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    mood: str
    entry_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Mood Ring fields
    sentiment: Optional[str] = None
    themes: Optional[List[str]] = None
    ai_summary: Optional[str] = None
    analyzed_at: Optional[datetime] = None


class StreakInfo(BaseModel):
    habit_id: str
    habit_name: str
    current_streak: int
    longest_streak: int


class StatsResponse(BaseModel):
    total_habits: int
    active_habits: int
    total_completions: int
    journal_entries: int
    best_streak: int


class AIRequest(BaseModel):
    prompt: str
    context: Optional[str] = None


class AIResponse(BaseModel):
    success: bool
    data: Optional[str] = None
    error: Optional[str] = None
