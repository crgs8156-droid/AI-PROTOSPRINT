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
from models_extended import (
    Friend, FriendRequest, FriendRequestCreate, SharedHabit, ShareHabitRequest,
    NotificationPreference, NotificationPreferenceUpdate, HabitTemplate, HabitCategory,
    BulkHabitCreate, ActivityItem, PasswordResetToken, ForgotPasswordRequest, ResetPasswordRequest
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from streak_calculator import calculate_streaks
from ai_service import ai_service
from export_service import export_service
from password_reset_service import password_reset_service
from fastapi.responses import Response


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
friends_collection = db.friends
friend_requests_collection = db.friend_requests
shared_habits_collection = db.shared_habits
notifications_collection = db.notification_preferences
templates_collection = db.habit_templates
categories_collection = db.habit_categories
reset_tokens_collection = db.password_reset_tokens

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



@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        # Find user by email
        user = await users_collection.find_one({"email": request.email}, {"_id": 0})
        if not user:
            # Don't reveal if email exists or not for security
            return {"success": True, "data": {"message": "If the email exists, a reset link has been sent"}}
        
        # Generate reset token
        token = password_reset_service.generate_reset_token()
        
        # Save token to database
        reset_token = PasswordResetToken(user_id=user['id'], token=token)
        token_dict = reset_token.model_dump()
        token_dict['created_at'] = token_dict['created_at'].isoformat()
        await reset_tokens_collection.insert_one(token_dict)
        
        # Send reset email (mock for now)
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        await password_reset_service.send_reset_email(request.email, token, frontend_url)
        
        return {"success": True, "data": {"message": "If the email exists, a reset link has been sent"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    try:
        # Find token
        token_doc = await reset_tokens_collection.find_one(
            {"token": request.token, "used": False},
            {"_id": 0}
        )
        if not token_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Check if token is expired (1 hour)
        created_at = datetime.fromisoformat(token_doc['created_at'])
        if password_reset_service.is_token_expired(created_at):
            raise HTTPException(status_code=400, detail="Reset token has expired")
        
        # Update user password
        new_hashed_password = hash_password(request.new_password)
        await users_collection.update_one(
            {"id": token_doc['user_id']},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        
        # Mark token as used
        await reset_tokens_collection.update_one(
            {"token": request.token},
            {"$set": {"used": True}}
        )
        
        return {"success": True, "data": {"message": "Password reset successfully"}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Auto-trigger AI analysis in background (Mood Ring feature)
        import asyncio
        asyncio.create_task(analyze_entry_background(entry_dict['id'], entry_data.content))
        
        return {"success": True, "data": response_data}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def analyze_entry_background(entry_id: str, content: str):
    """Background task to analyze journal entry."""
    try:
        analysis = await ai_service.analyze_journal_entry(content)
        await journal_collection.update_one(
            {"id": entry_id},
            {"$set": {
                "sentiment": analysis["sentiment"],
                "themes": analysis["themes"],
                "ai_summary": analysis["summary"],
                "analyzed_at": datetime.utcnow().isoformat()
            }}
        )
        print(f"✅ Analysis complete for entry {entry_id}: {analysis['sentiment']}")
    except Exception as e:
        print(f"❌ Failed to analyze entry {entry_id}: {str(e)}")


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



# ============= MOOD RING (EMOTIONAL ANALYSIS) ROUTES =============

@api_router.post("/ai/analyze-entry")
async def analyze_journal_entry(request: AIRequest, user_id: str = Depends(get_current_user)):
    """Analyze a journal entry for sentiment, themes, and summary."""
    try:
        import json
        data = json.loads(request.prompt)
        entry_id = data.get('entryId')
        content = data.get('content')
        
        # Get the journal entry to verify ownership
        entry = await journal_collection.find_one(
            {"id": entry_id, "user_id": user_id},
            {"_id": 0}
        )
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        
        # Run AI analysis
        analysis = await ai_service.analyze_journal_entry(content)
        
        # Update entry with analysis
        update_data = {
            "sentiment": analysis["sentiment"],
            "themes": analysis["themes"],
            "ai_summary": analysis["summary"],
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        await journal_collection.update_one(
            {"id": entry_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "data": {
                "sentiment": analysis["sentiment"],
                "themes": analysis["themes"],
                "ai_summary": analysis["summary"]
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/ai/analyze-batch")
async def analyze_batch_entries(user_id: str = Depends(get_current_user)):
    """Analyze all unanalyzed journal entries for the user."""
    try:
        # Get unanalyzed entries
        unanalyzed = await journal_collection.find({
            "user_id": user_id,
            "analyzed_at": {"$exists": False}
        }, {"_id": 0}).to_list(100)
        
        processed = 0
        failed = 0
        
        for entry in unanalyzed:
            try:
                # Run analysis
                analysis = await ai_service.analyze_journal_entry(entry['content'])
                
                # Update entry
                await journal_collection.update_one(
                    {"id": entry['id']},
                    {"$set": {
                        "sentiment": analysis["sentiment"],
                        "themes": analysis["themes"],
                        "ai_summary": analysis["summary"],
                        "analyzed_at": datetime.utcnow().isoformat()
                    }}
                )
                processed += 1
                
                # 500ms delay between calls as specified
                import asyncio
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Failed to analyze entry {entry['id']}: {str(e)}")
                failed += 1
        
        return {
            "success": True,
            "data": {
                "processed": processed,
                "failed": failed,
                "total": len(unanalyzed)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/ai/emotional-dashboard")
async def get_emotional_dashboard(user_id: str = Depends(get_current_user)):
    """Get emotional analysis data for the last 14 days."""
    try:
        # Get last 14 days entries
        start_date = (date.today() - timedelta(days=13)).isoformat()
        
        entries = await journal_collection.find({
            "user_id": user_id,
            "entry_date": {"$gte": start_date}
        }, {"_id": 0}).sort("entry_date", 1).to_list(100)
        
        # Filter to only include analyzed entries for the response
        dashboard_data = []
        for entry in entries:
            dashboard_data.append({
                "entry_date": entry.get("entry_date"),
                "sentiment": entry.get("sentiment"),
                "themes": entry.get("themes", []),
                "ai_summary": entry.get("ai_summary"),
                "mood": entry.get("mood"),
                "analyzed_at": entry.get("analyzed_at")
            })
        
        return {"success": True, "data": dashboard_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/ai/weekly-summary")
async def generate_weekly_summary(user_id: str = Depends(get_current_user)):
    """Generate AI summary of the week's emotional state."""
    try:
        # Get last 7 days entries
        start_date = (date.today() - timedelta(days=6)).isoformat()
        
        entries = await journal_collection.find({
            "user_id": user_id,
            "entry_date": {"$gte": start_date},
            "analyzed_at": {"$exists": True}
        }, {"_id": 0, "entry_date": 1, "sentiment": 1, "themes": 1, "ai_summary": 1}).sort("entry_date", 1).to_list(7)
        
        if not entries:
            return {
                "success": True,
                "data": {
                    "summary": "No journal entries found for the past week. Start journaling to see your emotional insights!"
                }
            }
        
        # Generate weekly summary
        summary = await ai_service.generate_weekly_summary(entries)
        
        return {
            "success": True,
            "data": {
                "summary": summary,
                "entries_count": len(entries),
                "date_range": f"{entries[0]['entry_date']} to {entries[-1]['entry_date']}"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}




# ============= SOCIAL FEATURES ROUTES =============

@api_router.get("/friends")
async def get_friends(user_id: str = Depends(get_current_user)):
    try:
        # Get all friend relationships
        friends = await friends_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        
        # Get friend details
        friend_list = []
        for friend in friends:
            friend_user = await users_collection.find_one({"id": friend['friend_id']}, {"_id": 0, "id": 1, "name": 1, "email": 1})
            if friend_user:
                friend_list.append(friend_user)
        
        return {"success": True, "data": friend_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/friends/request")
async def send_friend_request(request_data: FriendRequestCreate, user_id: str = Depends(get_current_user)):
    try:
        # Find user by email
        target_user = await users_collection.find_one({"email": request_data.friend_email}, {"_id": 0})
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if target_user['id'] == user_id:
            raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
        
        # Check if already friends
        existing = await friends_collection.find_one({
            "$or": [
                {"user_id": user_id, "friend_id": target_user['id']},
                {"user_id": target_user['id'], "friend_id": user_id}
            ]
        }, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Already friends")
        
        # Check for pending request
        pending = await friend_requests_collection.find_one({
            "$or": [
                {"from_user_id": user_id, "to_user_id": target_user['id'], "status": "pending"},
                {"from_user_id": target_user['id'], "to_user_id": user_id, "status": "pending"}
            ]
        }, {"_id": 0})
        if pending:
            raise HTTPException(status_code=400, detail="Friend request already pending")
        
        # Create request
        friend_request = FriendRequest(from_user_id=user_id, to_user_id=target_user['id'])
        request_dict = friend_request.model_dump()
        request_dict['created_at'] = request_dict['created_at'].isoformat()
        await friend_requests_collection.insert_one(request_dict)
        
        return {"success": True, "data": request_dict}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/friends/requests")
async def get_friend_requests(user_id: str = Depends(get_current_user)):
    try:
        requests = await friend_requests_collection.find({
            "to_user_id": user_id,
            "status": "pending"
        }, {"_id": 0}).to_list(100)
        
        # Get sender details
        for req in requests:
            sender = await users_collection.find_one({"id": req['from_user_id']}, {"_id": 0, "id": 1, "name": 1, "email": 1})
            req['sender'] = sender
        
        return {"success": True, "data": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/friends/requests/{request_id}/accept")
async def accept_friend_request(request_id: str, user_id: str = Depends(get_current_user)):
    try:
        request = await friend_requests_collection.find_one({"id": request_id, "to_user_id": user_id}, {"_id": 0})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Create friendship (both directions)
        friend1 = Friend(user_id=user_id, friend_id=request['from_user_id'])
        friend2 = Friend(user_id=request['from_user_id'], friend_id=user_id)
        
        friend1_dict = friend1.model_dump()
        friend1_dict['created_at'] = friend1_dict['created_at'].isoformat()
        friend2_dict = friend2.model_dump()
        friend2_dict['created_at'] = friend2_dict['created_at'].isoformat()
        
        await friends_collection.insert_many([friend1_dict, friend2_dict])
        
        # Update request status
        await friend_requests_collection.update_one(
            {"id": request_id},
            {"$set": {"status": "accepted"}}
        )
        
        return {"success": True, "data": {"message": "Friend request accepted"}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: str, user_id: str = Depends(get_current_user)):
    try:
        # Remove both directions
        await friends_collection.delete_many({
            "$or": [
                {"user_id": user_id, "friend_id": friend_id},
                {"user_id": friend_id, "friend_id": user_id}
            ]
        })
        return {"success": True, "data": {"message": "Friend removed"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/habits/share")
async def share_habit(share_data: ShareHabitRequest, user_id: str = Depends(get_current_user)):
    try:
        # Verify habit belongs to user
        habit = await habits_collection.find_one({"id": share_data.habit_id, "user_id": user_id}, {"_id": 0})
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        # Find friend
        friend = await users_collection.find_one({"email": share_data.friend_email}, {"_id": 0})
        if not friend:
            raise HTTPException(status_code=404, detail="Friend not found")
        
        # Create shared habit
        shared = SharedHabit(
            habit_id=share_data.habit_id,
            shared_by_user_id=user_id,
            shared_with_user_id=friend['id'],
            message=share_data.message
        )
        shared_dict = shared.model_dump()
        shared_dict['created_at'] = shared_dict['created_at'].isoformat()
        await shared_habits_collection.insert_one(shared_dict)
        
        return {"success": True, "data": shared_dict}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/social/feed")
async def get_activity_feed(user_id: str = Depends(get_current_user)):
    try:
        # Get friends
        friends = await friends_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        friend_ids = [f['friend_id'] for f in friends]
        friend_ids.append(user_id)  # Include own activity
        
        # Get recent completions from friends
        recent_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        completions = await completions_collection.find({
            "user_id": {"$in": friend_ids},
            "completed_date": {"$gte": recent_date}
        }, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
        
        # Build activity feed
        activities = []
        for comp in completions:
            user = await users_collection.find_one({"id": comp['user_id']}, {"_id": 0, "name": 1})
            habit = await habits_collection.find_one({"id": comp['habit_id']}, {"_id": 0, "name": 1, "emoji": 1})
            if user and habit:
                activities.append({
                    "user_name": user['name'],
                    "activity_type": "completed_habit",
                    "description": f"{habit['emoji']} {habit['name']}",
                    "timestamp": comp['created_at']
                })
        
        return {"success": True, "data": activities[:20]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= NOTIFICATIONS ROUTES =============

@api_router.get("/notifications/preferences")
async def get_notification_preferences(user_id: str = Depends(get_current_user)):
    try:
        prefs = await notifications_collection.find_one({"user_id": user_id}, {"_id": 0})
        if not prefs:
            # Create default preferences
            default_prefs = NotificationPreference(user_id=user_id)
            prefs_dict = default_prefs.model_dump()
            prefs_dict['updated_at'] = prefs_dict['updated_at'].isoformat()
            await notifications_collection.insert_one(prefs_dict)
            prefs = prefs_dict
        return {"success": True, "data": prefs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/notifications/preferences")
async def update_notification_preferences(prefs_data: NotificationPreferenceUpdate, user_id: str = Depends(get_current_user)):
    try:
        update_data = {k: v for k, v in prefs_data.model_dump().items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            await notifications_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data},
                upsert=True
            )
        
        updated = await notifications_collection.find_one({"user_id": user_id}, {"_id": 0})
        return {"success": True, "data": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= EXPORT ROUTES =============

@api_router.get("/export/habits/csv")
async def export_habits_csv(user_id: str = Depends(get_current_user)):
    try:
        habits = await habits_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        completions = await completions_collection.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        
        csv_data = export_service.generate_habits_csv(habits, completions)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=habits.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/habits/pdf")
async def export_habits_pdf(user_id: str = Depends(get_current_user)):
    try:
        user = await users_collection.find_one({"id": user_id}, {"_id": 0})
        habits = await habits_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        completions = await completions_collection.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        
        pdf_data = export_service.generate_habits_pdf(habits, completions, user['name'])
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=habits.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/journal/csv")
async def export_journal_csv(user_id: str = Depends(get_current_user)):
    try:
        entries = await journal_collection.find({"user_id": user_id}, {"_id": 0}).sort("entry_date", -1).to_list(1000)
        
        csv_data = export_service.generate_journal_csv(entries)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=journal.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/journal/pdf")
async def export_journal_pdf(user_id: str = Depends(get_current_user)):
    try:
        user = await users_collection.find_one({"id": user_id}, {"_id": 0})
        entries = await journal_collection.find({"user_id": user_id}, {"_id": 0}).sort("entry_date", -1).to_list(1000)
        
        pdf_data = export_service.generate_journal_pdf(entries, user['name'])
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=journal.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= TEMPLATES & CATEGORIES ROUTES =============

@api_router.get("/categories")
async def get_categories(user_id: str = Depends(get_current_user)):
    try:
        categories = await categories_collection.find({}, {"_id": 0}).to_list(100)
        return {"success": True, "data": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/templates")
async def get_templates(category_id: Optional[str] = None, user_id: str = Depends(get_current_user)):
    try:
        query = {"category_id": category_id} if category_id else {}
        templates = await templates_collection.find(query, {"_id": 0}).to_list(100)
        return {"success": True, "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/habits/bulk")
async def create_habits_from_templates(bulk_data: BulkHabitCreate, user_id: str = Depends(get_current_user)):
    try:
        created_habits = []
        for template_id in bulk_data.template_ids:
            template = await templates_collection.find_one({"id": template_id}, {"_id": 0})
            if template:
                habit = Habit(
                    user_id=user_id,
                    name=template['name'],
                    emoji=template['emoji'],
                    color=template['color']
                )
                habit_dict = habit.model_dump()
                habit_dict['created_at'] = habit_dict['created_at'].isoformat()
                await habits_collection.insert_one(habit_dict)
                created_habits.append(habit_dict)
        
        return {"success": True, "data": created_habits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
