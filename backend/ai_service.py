from dotenv import load_dotenv
import os
from pathlib import Path
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


class AIService:
    def __init__(self):
        self.api_key = EMERGENT_LLM_KEY
    
    async def summarize_journal(self, content: str) -> str:
        """Summarize a journal entry using Claude."""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id="journal_summarize",
                system_message="You are a helpful assistant that summarizes journal entries. Provide a concise, empathetic summary in 2-3 sentences."
            ).with_model("anthropic", "claude-sonnet-4-6")
            
            message = UserMessage(text=f"Summarize this journal entry:\n\n{content}")
            response = await chat.send_message(message)
            return response
        except Exception as e:
            return f"Error summarizing: {str(e)}"
    
    async def get_habit_insights(self, habit_data: dict) -> str:
        """Generate insights about habit patterns using Gemini."""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id="habit_insights",
                system_message="You are a habit coach. Analyze habit completion patterns and provide encouraging, actionable insights."
            ).with_model("gemini", "gemini-3-flash-preview")
            
            prompt = f"""Analyze this habit data and provide insights:
            
Habit: {habit_data.get('name')}
Current Streak: {habit_data.get('current_streak')} days
Longest Streak: {habit_data.get('longest_streak')} days
Total Completions: {habit_data.get('total_completions')}

Provide 2-3 sentences of encouraging insights and suggestions."""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            return response
        except Exception as e:
            return f"Error generating insights: {str(e)}"
    
    async def coach_user(self, user_context: str) -> str:
        """Provide coaching message based on user data."""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id="user_coach",
                system_message="You are a supportive life coach focused on habits and personal growth. Be encouraging, specific, and actionable."
            ).with_model("anthropic", "claude-sonnet-4-6")
            
            message = UserMessage(text=user_context)
            response = await chat.send_message(message)
            return response
        except Exception as e:
            return f"Error coaching: {str(e)}"
    
    async def analyze_mood(self, entries: list) -> str:
        """Analyze mood patterns from journal entries."""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id="mood_analyze",
                system_message="You are a wellness analyst. Identify mood patterns and provide supportive observations."
            ).with_model("gemini", "gemini-3-flash-preview")
            
            mood_summary = "\n".join([f"- {e['date']}: {e['mood']}" for e in entries])
            prompt = f"Analyze these mood patterns from the last 14 days:\n\n{mood_summary}\n\nProvide a brief analysis and supportive suggestions."
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            return response
        except Exception as e:
            return f"Error analyzing mood: {str(e)}"
    
    async def chat_with_context(self, user_message: str, context: str = "") -> str:
        """General chat with user context."""
        try:
            system_msg = "You are a helpful AI assistant for a habit tracking and journaling app. Help users with their habits, goals, and personal growth."
            if context:
                system_msg += f" Context: {context}"
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="general_chat",
                system_message=system_msg
            ).with_model("anthropic", "claude-sonnet-4-6")
            
            message = UserMessage(text=user_message)
            response = await chat.send_message(message)
            return response
        except Exception as e:
            return f"Error in chat: {str(e)}"


ai_service = AIService()
