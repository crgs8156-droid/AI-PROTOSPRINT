from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date, timedelta
import os
import logging
from pathlib import Path
from typing import List, Optional

from models import (
    UserCreate, UserLogin, User, UserInDB, Habit, HabitCreate, HabitUpdate,
    Completion, CompletionCreate, JournalEntry, JournalEntryCreate, 
    JournalEntryUpdate, StreakInfo, StatsResponse, AIRequest, AIResponse
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from streak_calculator import calculate_streaks
from ai_service import ai_service


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collections
users_collection = db.users
habits_collection = db.habits
completions_collection = db.completions
journal_collection = db.journal_entries

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============= AUTH ROUTES =============

@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    try:
        # Check if user exists
        existing_user = await users_collection.find_one({"email": user_data.email}, {"_id": 0})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        hashed_pwd = hash_password(user_data.password)
        user_dict = UserInDB(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_pwd
        ).model_dump()
        
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await users_collection.insert_one(user_dict)
        
        # Create token
        token = create_access_token({"user_id": user_dict['id'], "email": user_dict['email']})
        
        return {
            "success": True,
            "data": {
                "user": User(**user_dict).model_dump(),
                "token": token
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    try:
        user = await users_collection.find_one({"email": credentials.email}, {"_id": 0})
        if not user or not verify_password(credentials.password, user['hashed_password']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_access_token({"user_id": user['id'], "email": user['email']})
        
        return {
            "success": True,
            "data": {
                "user": User(**user).model_dump(),
                "token": token
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auth/me")
async def get_me(user_id: str = Depends(get_current_user)):
    try:
        user = await users_collection.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": User(**user).model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    return {"success": True, "data": {"message": "Logged out successfully"}}


# ============= HABITS ROUTES =============

@api_router.get("/habits", response_model=dict)
async def get_habits(user_id: str = Depends(get_current_user)):
    try:
        habits = await habits_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        return {"success": True, "data": habits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/habits")
async def create_habit(habit_data: HabitCreate, user_id: str = Depends(get_current_user)):
    try:
        habit_dict = Habit(user_id=user_id, **habit_data.model_dump()).model_dump()
        habit_dict['created_at'] = habit_dict['created_at'].isoformat()
        
        # Store a copy before inserting to avoid ObjectId in response
        response_data = habit_dict.copy()
        await habits_collection.insert_one(habit_dict)
        return {"success": True, "data": response_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/habits/{habit_id}")
async def update_habit(habit_id: str, habit_data: HabitUpdate, user_id: str = Depends(get_current_user)):
    try:
        habit = await habits_collection.find_one({"id": habit_id, "user_id": user_id}, {"_id": 0})
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        update_data = {k: v for k, v in habit_data.model_dump().items() if v is not None}
        if update_data:
            await habits_collection.update_one({"id": habit_id}, {"$set": update_data})
        
        updated_habit = await habits_collection.find_one({"id": habit_id}, {"_id": 0})
        return {"success": True, "data": updated_habit}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/habits/{habit_id}")
async def delete_habit(habit_id: str, user_id: str = Depends(get_current_user)):
    try:
        result = await habits_collection.delete_one({"id": habit_id, "user_id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        # Also delete all completions for this habit
        await completions_collection.delete_many({"habit_id": habit_id})
        
        return {"success": True, "data": {"message": "Habit deleted"}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.patch("/habits/{habit_id}/toggle")
async def toggle_habit(habit_id: str, user_id: str = Depends(get_current_user)):
    try:
        habit = await habits_collection.find_one({"id": habit_id, "user_id": user_id}, {"_id": 0})
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        new_status = not habit.get('is_active', True)
        await habits_collection.update_one({"id": habit_id}, {"$set": {"is_active": new_status}})
        
        updated_habit = await habits_collection.find_one({"id": habit_id}, {"_id": 0})
        return {"success": True, "data": updated_habit}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= COMPLETIONS ROUTES =============

@api_router.get("/completions/today")
async def get_today_completions(user_id: str = Depends(get_current_user)):
    try:
        today = date.today().isoformat()
        completions = await completions_collection.find(
            {"user_id": user_id, "completed_date": today}, 
            {"_id": 0}
        ).to_list(100)
        return {"success": True, "data": completions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/completions/{habit_id}")
async def get_habit_completions(habit_id: str, user_id: str = Depends(get_current_user)):
    try:
        completions = await completions_collection.find(
            {"habit_id": habit_id, "user_id": user_id},
            {"_id": 0}
        ).to_list(1000)
        return {"success": True, "data": completions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/completions")
async def mark_complete(completion_data: CompletionCreate, user_id: str = Depends(get_current_user)):
    try:
        # Verify habit belongs to user
        habit = await habits_collection.find_one(
            {"id": completion_data.habit_id, "user_id": user_id}, 
            {"_id": 0}
        )
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        completed_date = completion_data.completed_date or date.today()
        
        # Check if already completed
        existing = await completions_collection.find_one({
            "habit_id": completion_data.habit_id,
            "completed_date": completed_date.isoformat()
        }, {"_id": 0})
        
        if existing:
            return {"success": True, "data": existing}
        
        completion_dict = Completion(
            habit_id=completion_data.habit_id,
            user_id=user_id,
            completed_date=completed_date
        ).model_dump()
        
        completion_dict['completed_date'] = completion_dict['completed_date'].isoformat()
        completion_dict['created_at'] = completion_dict['created_at'].isoformat()
        
        # Store a copy before inserting to avoid ObjectId in response
        response_data = completion_dict.copy()
        await completions_collection.insert_one(completion_dict)
        return {"success": True, "data": response_data}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/completions/{habit_id}/today")
async def unmark_complete(habit_id: str, user_id: str = Depends(get_current_user)):
    try:
        today = date.today().isoformat()
        result = await completions_collection.delete_one({
            "habit_id": habit_id,
            "user_id": user_id,
            "completed_date": today
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Completion not found")
        
        return {"success": True, "data": {"message": "Completion removed"}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/completions/history/{days}")
async def get_completion_history(days: int, user_id: str = Depends(get_current_user)):
    try:
        start_date = (date.today() - timedelta(days=days)).isoformat()
        completions = await completions_collection.find(
            {"user_id": user_id, "completed_date": {"$gte": start_date}},
            {"_id": 0}
        ).to_list(1000)
        return {"success": True, "data": completions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= JOURNAL ROUTES =============

@api_router.get("/journal")
async def get_journal_entries(skip: int = 0, limit: int = 50, user_id: str = Depends(get_current_user)):
    try:
        entries = await journal_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("entry_date", -1).skip(skip).limit(limit).to_list(limit)
        return {"success": True, "data": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/journal/{entry_id}")
async def get_journal_entry(entry_id: str, user_id: str = Depends(get_current_user)):
    try:
        entry = await journal_collection.find_one(
            {"id": entry_id, "user_id": user_id},
            {"_id": 0}
        )
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return {"success": True, "data": entry}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/journal/date/{entry_date}")
async def get_journal_by_date(entry_date: str, user_id: str = Depends(get_current_user)):
    try:
        entry = await journal_collection.find_one(
            {"user_id": user_id, "entry_date": entry_date},
            {"_id": 0}
        )
        if not entry:
            raise HTTPException(status_code=404, detail="No entry for this date")
        return {"success": True, "data": entry}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/journal")
async def create_journal_entry(entry_data: JournalEntryCreate, user_id: str = Depends(get_current_user)):
    try:
        entry_date = entry_data.entry_date or date.today()
        
        # Check if entry already exists for this date
        existing = await journal_collection.find_one({
            "user_id": user_id,
            "entry_date": entry_date.isoformat()
        }, {"_id": 0})
        
        if existing:
            raise HTTPException(status_code=400, detail="Entry already exists for this date")
        
        entry_dict = JournalEntry(
            user_id=user_id,
            content=entry_data.content,
            mood=entry_data.mood,
            entry_date=entry_date
        ).model_dump()
        
        entry_dict['entry_date'] = entry_dict['entry_date'].isoformat()
        entry_dict['created_at'] = entry_dict['created_at'].isoformat()
        entry_dict['updated_at'] = entry_dict['updated_at'].isoformat()
        
        # Store a copy before inserting to avoid ObjectId in response
        response_data = entry_dict.copy()
        await journal_collection.insert_one(entry_dict)
        return {"success": True, "data": response_data}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/journal/{entry_id}")
async def update_journal_entry(entry_id: str, entry_data: JournalEntryUpdate, user_id: str = Depends(get_current_user)):
    try:
        entry = await journal_collection.find_one(
            {"id": entry_id, "user_id": user_id},
            {"_id": 0}
        )
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        
        update_data = {k: v for k, v in entry_data.model_dump().items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            await journal_collection.update_one({"id": entry_id}, {"$set": update_data})
        
        updated_entry = await journal_collection.find_one({"id": entry_id}, {"_id": 0})
        return {"success": True, "data": updated_entry}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str, user_id: str = Depends(get_current_user)):
    try:
        result = await journal_collection.delete_one({"id": entry_id, "user_id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return {"success": True, "data": {"message": "Entry deleted"}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= STATS ROUTES =============

@api_router.get("/stats/streaks")
async def get_streaks(user_id: str = Depends(get_current_user)):
    try:
        habits = await habits_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        
        streaks = []
        for habit in habits:
            completions = await completions_collection.find(
                {"habit_id": habit['id']},
                {"_id": 0, "completed_date": 1}
            ).to_list(1000)
            
            completion_dates = [
                datetime.fromisoformat(c['completed_date']).date() 
                for c in completions
            ]
            
            streak_data = calculate_streaks(completion_dates)
            streaks.append({
                "habit_id": habit['id'],
                "habit_name": habit['name'],
                "current_streak": streak_data['current_streak'],
                "longest_streak": streak_data['longest_streak']
            })
        
        return {"success": True, "data": streaks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/stats/summary")
async def get_stats_summary(user_id: str = Depends(get_current_user)):
    try:
        total_habits = await habits_collection.count_documents({"user_id": user_id})
        active_habits = await habits_collection.count_documents({"user_id": user_id, "is_active": True})
        total_completions = await completions_collection.count_documents({"user_id": user_id})
        journal_entries = await journal_collection.count_documents({"user_id": user_id})
        
        # Get best streak
        habits = await habits_collection.find({"user_id": user_id}, {"_id": 0, "id": 1}).to_list(100)
        best_streak = 0
        
        for habit in habits:
            completions = await completions_collection.find(
                {"habit_id": habit['id']},
                {"_id": 0, "completed_date": 1}
            ).to_list(1000)
            
            completion_dates = [
                datetime.fromisoformat(c['completed_date']).date() 
                for c in completions
            ]
            
            streak_data = calculate_streaks(completion_dates)
            best_streak = max(best_streak, streak_data['longest_streak'])
        
        return {
            "success": True,
            "data": {
                "total_habits": total_habits,
                "active_habits": active_habits,
                "total_completions": total_completions,
                "journal_entries": journal_entries,
                "best_streak": best_streak
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/stats/calendar/{year}/{month}")
async def get_calendar_data(year: int, month: int, user_id: str = Depends(get_current_user)):
    try:
        # Get all completions for the month
        start_date = date(year, month, 1).isoformat()
        if month == 12:
            end_date = date(year + 1, 1, 1).isoformat()
        else:
            end_date = date(year, month + 1, 1).isoformat()
        
        completions = await completions_collection.find(
            {
                "user_id": user_id,
                "completed_date": {"$gte": start_date, "$lt": end_date}
            },
            {"_id": 0}
        ).to_list(1000)
        
        return {"success": True, "data": completions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= AI ROUTES =============

@api_router.post("/ai/summarize")
async def summarize_journal(request: AIRequest, user_id: str = Depends(get_current_user)):
    try:
        result = await ai_service.summarize_journal(request.prompt)
        return AIResponse(success=True, data=result)
    except Exception as e:
        return AIResponse(success=False, error=str(e))


@api_router.post("/ai/insights")
async def get_habit_insights(request: AIRequest, user_id: str = Depends(get_current_user)):
    try:
        import json
        habit_data = json.loads(request.prompt)
        result = await ai_service.get_habit_insights(habit_data)
        return AIResponse(success=True, data=result)
    except Exception as e:
        return AIResponse(success=False, error=str(e))


@api_router.post("/ai/coach")
async def coach_user(request: AIRequest, user_id: str = Depends(get_current_user)):
    try:
        result = await ai_service.coach_user(request.prompt)
        return AIResponse(success=True, data=result)
    except Exception as e:
        return AIResponse(success=False, error=str(e))


@api_router.post("/ai/analyze")
async def analyze_mood(request: AIRequest, user_id: str = Depends(get_current_user)):
    try:
        import json
        entries = json.loads(request.prompt)
        result = await ai_service.analyze_mood(entries)
        return AIResponse(success=True, data=result)
    except Exception as e:
        return AIResponse(success=False, error=str(e))


@api_router.post("/ai/chat")
async def ai_chat(request: AIRequest, user_id: str = Depends(get_current_user)):
    try:
        result = await ai_service.chat_with_context(request.prompt, request.context or "")
        return AIResponse(success=True, data=result)
    except Exception as e:
        return AIResponse(success=False, error=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
