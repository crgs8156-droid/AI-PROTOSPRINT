import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.auth import hash_password
from backend.models import User, Habit, Completion, JournalEntry

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


async def seed_database():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Starting database seed...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.habits.delete_many({})
    await db.completions.delete_many({})
    await db.journal_entries.delete_many({})
    
    # Create demo user
    demo_user = User(
        name="Alex Johnson",
        email="demo@dailyroutine.com"
    )
    user_dict = demo_user.model_dump()
    user_dict['hashed_password'] = hash_password("Demo@1234")
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    user_id = user_dict['id']
    
    print(f"✅ Created user: {demo_user.email}")
    
    # Create 5 habits
    habits_data = [
        {"name": "Read 20 pages", "emoji": "📚", "color": "#7C3AED"},
        {"name": "Meditation", "emoji": "🧘", "color": "#0EA5E9"},
        {"name": "Exercise", "emoji": "💪", "color": "#10B981"},
        {"name": "Drink 8 glasses of water", "emoji": "💧", "color": "#F59E0B"},
        {"name": "Sleep by 11 PM", "emoji": "🛌", "color": "#EC4899"},
    ]
    
    habits = []
    for habit_data in habits_data:
        habit = Habit(user_id=user_id, **habit_data)
        habit_dict = habit.model_dump()
        habit_dict['created_at'] = habit_dict['created_at'].isoformat()
        await db.habits.insert_one(habit_dict)
        habits.append(habit_dict)
    
    print(f"✅ Created {len(habits)} habits")
    
    # Create 14 days of habit completions with realistic patterns
    completion_patterns = {
        habits[0]['id']: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1],  # Read - strong streak
        habits[1]['id']: [1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],  # Meditation - good
        habits[2]['id']: [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1],  # Exercise - moderate
        habits[3]['id']: [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1],  # Water - good
        habits[4]['id']: [1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1],  # Sleep - moderate
    }
    
    total_completions = 0
    for habit_id, pattern in completion_patterns.items():
        for i, completed in enumerate(pattern):
            if completed:
                completion_date = date.today() - timedelta(days=13-i)
                completion = Completion(
                    habit_id=habit_id,
                    user_id=user_id,
                    completed_date=completion_date
                )
                completion_dict = completion.model_dump()
                completion_dict['completed_date'] = completion_dict['completed_date'].isoformat()
                completion_dict['created_at'] = completion_dict['created_at'].isoformat()
                await db.completions.insert_one(completion_dict)
                total_completions += 1
    
    print(f"✅ Created {total_completions} habit completions")
    
    # Create 14 days of journal entries
    journal_entries_data = [
        {
            "mood": "Happy",
            "content": "Today was incredible! Started my morning with a refreshing meditation session that really set the tone for the day. I managed to finish three chapters of the book I've been reading, and it's fascinating how the author weaves complex ideas into simple narratives. Went for a long walk in the park during lunch, and the weather was perfect. I'm feeling grateful for these small moments of peace and the progress I'm making on my goals. It's amazing how consistent daily habits compound over time."
        },
        {
            "mood": "Energized",
            "content": "Woke up feeling incredibly motivated today! Hit the gym early morning and crushed my workout routine. There's something about physical exercise that just clears my mind and energizes my entire being. Spent the afternoon working on a personal project I've been passionate about, and I'm finally starting to see real progress. Had a great conversation with an old friend who reminded me of how far I've come. Ending the day feeling accomplished and ready to tackle tomorrow's challenges."
        },
        {
            "mood": "Neutral",
            "content": "A pretty standard day today. Nothing particularly exciting happened, but nothing bad either. Stuck to my usual routine - meditation, reading, and some exercise. Sometimes these ordinary days are necessary to recharge. I've been thinking about my long-term goals and whether I need to adjust my approach. Not feeling stuck, just contemplative. Made myself a nice dinner and watched a documentary about ocean life. It's peaceful to have these quiet, uneventful days occasionally."
        },
        {
            "mood": "Anxious",
            "content": "Feeling a bit overwhelmed today. There's so much I want to accomplish, and sometimes it feels like time is moving too fast. I did manage to stick to my morning routine, which helped ground me a bit. Reading has been my escape - losing myself in another world for a while helps calm my racing thoughts. I know these feelings will pass, and I'm trying to be patient with myself. Journaling is helping me process these emotions. Tomorrow is a new day, and I'll approach it with renewed focus."
        },
        {
            "mood": "Happy",
            "content": "What a wonderful day! Finally broke through a plateau I've been struggling with in my fitness journey. It's such a good reminder that persistence pays off. My meditation practice is really starting to feel natural now, not something I have to force myself to do. I'm learning so much from the books I'm reading about personal development and mindfulness. Had a meaningful conversation with a family member that brought us closer. Feeling blessed and optimistic about the future."
        },
        {
            "mood": "Sad",
            "content": "Today was tough. Missing some people who are no longer in my life, and sometimes grief just hits unexpectedly. I tried to honor my feelings while still maintaining my routines. Meditation was particularly challenging today - my mind kept wandering to memories and what-ifs. I know it's important to feel these emotions rather than suppress them. Reading provided some comfort, as did a long, contemplative walk. Tomorrow will be better, and I'm grateful I have these healthy coping mechanisms."
        },
        {
            "mood": "Energized",
            "content": "Absolutely buzzing with energy today! Everything just clicked - my workout felt effortless, work was productive, and I had the mental clarity to tackle some challenging problems. Started a new book that's already gripping my attention. It's days like these that remind me why I maintain these daily habits. The compound effect is real. I can see how much stronger, mentally and physically, I've become over the past few months. Celebrating these wins, big and small!"
        },
        {
            "mood": "Neutral",
            "content": "A balanced day today. Not spectacular, but solid. Completed all my habit goals without much struggle, which shows how much they've become second nature. Had some interesting insights during my reading time about habit formation and neuroplasticity. It's fascinating how our brains adapt and change. Spent the evening organizing my thoughts and planning for the week ahead. Sometimes these calm, reflective days are exactly what's needed for sustainable progress."
        },
        {
            "mood": "Happy",
            "content": "Feeling really content today. Had a breakthrough in understanding a concept I've been studying for weeks. My meditation practice continues to deepen, and I'm noticing how much more present I am in daily activities. Exercise was great - tried a new routine and loved it. Celebrated a friend's success today, which reminded me how important community is. Gratitude is the theme of today - grateful for health, habits, and the opportunity to keep growing."
        },
        {
            "mood": "Anxious",
            "content": "Another day of battling with anxious thoughts. The future feels uncertain, and I'm trying not to let worry consume me. My habits are anchors in the storm - they give me something concrete to focus on when everything else feels chaotic. Reading helps transport me away from my worries, even if temporarily. I'm learning that anxiety is part of the human experience, and resisting it only makes it stronger. Trying to observe these feelings with curiosity rather than judgment."
        },
        {
            "mood": "Energized",
            "content": "Today I felt unstoppable! Everything aligned perfectly. Morning meditation was profound - I reached a state of calm I rarely experience. My workout was challenging but rewarding, and I'm seeing real physical changes. The book I'm reading is transforming my perspective on personal growth. Had several meaningful interactions today that left me feeling connected and inspired. This is what living intentionally feels like, and I'm here for it!"
        },
        {
            "mood": "Happy",
            "content": "Simple pleasures made today special. A beautiful sunrise during my morning walk, a particularly good cup of coffee, and a chapter that moved me to tears. Sometimes happiness isn't about big achievements but appreciating the small, beautiful moments that fill our days. My habits have become rituals that I genuinely look forward to, not chores to check off. Ending the day feeling peaceful and satisfied with the life I'm building, one day at a time."
        },
        {
            "mood": "Neutral",
            "content": "A reflective day today. Been thinking about my journey over the past few months and how much has changed. The habits I've built are transforming not just my actions but my identity. I'm becoming the person I always wanted to be, slowly but surely. Had some quiet time to just be with my thoughts, no pressure to be productive or achieve anything specific. These moments of stillness are becoming just as valuable as the active pursuit of goals."
        },
        {
            "mood": "Happy",
            "content": "Ending this two-week period on a high note! Looking back at my journal entries, I can see the ups and downs, but overall trajectory is positive. My consistency with daily habits has been strong, and I'm proud of that. Even on difficult days, I showed up for myself. Learned so much from my reading, grew stronger through exercise, and found peace in meditation. Excited to continue this journey and see where these small daily actions lead me in the months ahead!"
        }
    ]
    
    for i, entry_data in enumerate(journal_entries_data):
        entry_date = date.today() - timedelta(days=13-i)
        entry = JournalEntry(
            user_id=user_id,
            entry_date=entry_date,
            **entry_data
        )
        entry_dict = entry.model_dump()
        entry_dict['entry_date'] = entry_dict['entry_date'].isoformat()
        entry_dict['created_at'] = entry_dict['created_at'].isoformat()
        entry_dict['updated_at'] = entry_dict['updated_at'].isoformat()
        await db.journal_entries.insert_one(entry_dict)
    
    print(f"✅ Created {len(journal_entries_data)} journal entries")
    
    print(f"\n🎉 Seeded: 1 user, {len(habits)} habits, {total_completions} completions, {len(journal_entries_data)} journal entries")
    print(f"\n📧 Demo login: demo@dailyroutine.com / Demo@1234")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
