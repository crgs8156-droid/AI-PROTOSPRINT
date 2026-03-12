#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, List

class DailyRoutineAPITester:
    def __init__(self, base_url="https://v1-main-dailyroutine.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Demo user credentials
        self.demo_email = "demo@dailyroutine.com"
        self.demo_password = "Demo@1234"
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {details}")
        else:
            print(f"❌ {name}: FAILED {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })
    
    def run_request(self, method: str, endpoint: str, data=None, expected_status=200) -> tuple:
        """Run HTTP request and return success, response"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            try:
                return success, response.json()
            except json.JSONDecodeError:
                return success, {"text_response": response.text}
                
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
    
    def test_auth_flow(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication...")
        
        # Test login with demo user
        success, response = self.run_request(
            'POST', 'auth/login',
            {'email': self.demo_email, 'password': self.demo_password}
        )
        
        if success and response.get('success'):
            self.token = response['data']['token']
            self.user_id = response['data']['user']['id']
            self.log_test("Login with demo user", True, f"Token received")
        else:
            self.log_test("Login with demo user", False, f"Response: {response}")
            return False
        
        # Test get current user
        success, response = self.run_request('GET', 'auth/me')
        if success and response.get('success'):
            user_data = response['data']
            self.log_test("Get current user", True, f"User: {user_data['email']}")
        else:
            self.log_test("Get current user", False, f"Response: {response}")
            
        return True
    
    def test_habits_crud(self):
        """Test habits CRUD operations"""
        print("\n📋 Testing Habits CRUD...")
        
        # Get existing habits
        success, response = self.run_request('GET', 'habits')
        if success and response.get('success'):
            existing_habits = response['data']
            self.log_test("Get habits", True, f"Found {len(existing_habits)} habits")
        else:
            self.log_test("Get habits", False, f"Response: {response}")
            return []
        
        # Create new habit
        new_habit_data = {
            "name": "Test Habit",
            "emoji": "🧪",
            "color": "#3B82F6"
        }
        success, response = self.run_request('POST', 'habits', new_habit_data, 200)
        if success and response.get('success'):
            habit_id = response['data']['id']
            self.log_test("Create habit", True, f"Created habit: {habit_id}")
        else:
            self.log_test("Create habit", False, f"Response: {response}")
            return existing_habits
        
        # Update habit
        update_data = {"name": "Updated Test Habit", "color": "#EF4444"}
        success, response = self.run_request('PUT', f'habits/{habit_id}', update_data)
        if success and response.get('success'):
            self.log_test("Update habit", True, f"Updated habit name and color")
        else:
            self.log_test("Update habit", False, f"Response: {response}")
        
        # Toggle habit active status
        success, response = self.run_request('PATCH', f'habits/{habit_id}/toggle')
        if success and response.get('success'):
            self.log_test("Toggle habit status", True, f"Toggled active status")
        else:
            self.log_test("Toggle habit status", False, f"Response: {response}")
        
        # Delete test habit
        success, response = self.run_request('DELETE', f'habits/{habit_id}')
        if success and response.get('success'):
            self.log_test("Delete habit", True, f"Deleted test habit")
        else:
            self.log_test("Delete habit", False, f"Response: {response}")
            
        return existing_habits
    
    def test_completions(self, habits: List[Dict]):
        """Test habit completions"""
        print("\n✅ Testing Habit Completions...")
        
        if not habits:
            self.log_test("Completions test", False, "No habits available for testing")
            return
        
        habit_id = habits[0]['id']
        
        # Get today's completions
        success, response = self.run_request('GET', 'completions/today')
        if success and response.get('success'):
            today_completions = response['data']
            self.log_test("Get today's completions", True, f"Found {len(today_completions)} completions")
        else:
            self.log_test("Get today's completions", False, f"Response: {response}")
        
        # Mark habit as complete
        completion_data = {"habit_id": habit_id}
        success, response = self.run_request('POST', 'completions', completion_data, 200)
        if success and response.get('success'):
            self.log_test("Mark habit complete", True, f"Marked habit {habit_id} complete")
        else:
            self.log_test("Mark habit complete", False, f"Response: {response}")
        
        # Get habit completions history
        success, response = self.run_request('GET', f'completions/{habit_id}')
        if success and response.get('success'):
            habit_completions = response['data']
            self.log_test("Get habit completions", True, f"Found {len(habit_completions)} completions")
        else:
            self.log_test("Get habit completions", False, f"Response: {response}")
        
        # Get completion history (last 30 days)
        success, response = self.run_request('GET', 'completions/history/30')
        if success and response.get('success'):
            history = response['data']
            self.log_test("Get completion history", True, f"Found {len(history)} completions in last 30 days")
        else:
            self.log_test("Get completion history", False, f"Response: {response}")
        
        # Unmark habit completion
        success, response = self.run_request('DELETE', f'completions/{habit_id}/today')
        if success and response.get('success'):
            self.log_test("Unmark habit completion", True, f"Unmarked habit {habit_id}")
        else:
            # This might fail if the completion was already there, which is OK
            self.log_test("Unmark habit completion", False, f"Response: {response}")
    
    def test_journal_crud(self):
        """Test journal entries CRUD"""
        print("\n📝 Testing Journal CRUD...")
        
        # Get existing journal entries
        success, response = self.run_request('GET', 'journal?limit=10')
        if success and response.get('success'):
            existing_entries = response['data']
            self.log_test("Get journal entries", True, f"Found {len(existing_entries)} entries")
        else:
            self.log_test("Get journal entries", False, f"Response: {response}")
            return
        
        # Create new journal entry with unique date
        test_date = date.today() + timedelta(days=1)  # Use tomorrow to avoid conflicts
        entry_data = {
            "content": "This is a test journal entry for API testing.",
            "mood": "Happy",
            "entry_date": test_date.isoformat()
        }
        success, response = self.run_request('POST', 'journal', entry_data, 200)
        if success and response.get('success'):
            entry_id = response['data']['id']
            self.log_test("Create journal entry", True, f"Created entry: {entry_id}")
        else:
            self.log_test("Create journal entry", False, f"Response: {response}")
            return
        
        # Get specific journal entry
        success, response = self.run_request('GET', f'journal/{entry_id}')
        if success and response.get('success'):
            entry = response['data']
            self.log_test("Get journal entry", True, f"Retrieved entry: {entry['mood']}")
        else:
            self.log_test("Get journal entry", False, f"Response: {response}")
        
        # Get journal entry by date
        success, response = self.run_request('GET', f'journal/date/{test_date.isoformat()}')
        if success and response.get('success'):
            entry = response['data']
            self.log_test("Get journal by date", True, f"Found entry for {test_date}")
        else:
            self.log_test("Get journal by date", False, f"Response: {response}")
        
        # Update journal entry
        update_data = {
            "content": "Updated test journal entry content.",
            "mood": "Excited"
        }
        success, response = self.run_request('PUT', f'journal/{entry_id}', update_data)
        if success and response.get('success'):
            self.log_test("Update journal entry", True, f"Updated entry mood and content")
        else:
            self.log_test("Update journal entry", False, f"Response: {response}")
        
        # Delete test journal entry
        success, response = self.run_request('DELETE', f'journal/{entry_id}')
        if success and response.get('success'):
            self.log_test("Delete journal entry", True, f"Deleted test entry")
        else:
            self.log_test("Delete journal entry", False, f"Response: {response}")
    
    def test_stats_and_streaks(self):
        """Test stats and streaks calculations"""
        print("\n📊 Testing Stats and Streaks...")
        
        # Get streaks
        success, response = self.run_request('GET', 'stats/streaks')
        if success and response.get('success'):
            streaks = response['data']
            self.log_test("Get streaks", True, f"Found {len(streaks)} habit streaks")
        else:
            self.log_test("Get streaks", False, f"Response: {response}")
        
        # Get stats summary
        success, response = self.run_request('GET', 'stats/summary')
        if success and response.get('success'):
            stats = response['data']
            self.log_test("Get stats summary", True, f"Total habits: {stats.get('total_habits')}, Best streak: {stats.get('best_streak')}")
        else:
            self.log_test("Get stats summary", False, f"Response: {response}")
        
        # Get calendar data for current month
        now = datetime.now()
        success, response = self.run_request('GET', f'stats/calendar/{now.year}/{now.month}')
        if success and response.get('success'):
            calendar_data = response['data']
            self.log_test("Get calendar data", True, f"Found {len(calendar_data)} completions this month")
        else:
            self.log_test("Get calendar data", False, f"Response: {response}")
    
    def test_ai_features(self):
        """Test AI features"""
        print("\n🤖 Testing AI Features...")
        
        # Test journal summarization
        ai_request = {"prompt": "Today I woke up early and went for a run. I felt great and accomplished. Then I had a healthy breakfast and started working on my projects."}
        success, response = self.run_request('POST', 'ai/summarize', ai_request)
        if success and response.get('success'):
            self.log_test("AI Journal Summarize", True, f"Generated summary")
        else:
            self.log_test("AI Journal Summarize", False, f"Response: {response}")
        
        # Test habit insights
        habit_data = {
            "name": "Morning Exercise",
            "current_streak": 5,
            "longest_streak": 12,
            "total_completions": 25
        }
        ai_request = {"prompt": json.dumps(habit_data)}
        success, response = self.run_request('POST', 'ai/insights', ai_request)
        if success and response.get('success'):
            self.log_test("AI Habit Insights", True, f"Generated insights")
        else:
            self.log_test("AI Habit Insights", False, f"Response: {response}")
        
        # Test coaching
        ai_request = {"prompt": "I'm struggling to maintain my daily reading habit. Any advice?"}
        success, response = self.run_request('POST', 'ai/coach', ai_request)
        if success and response.get('success'):
            self.log_test("AI Coaching", True, f"Generated coaching response")
        else:
            self.log_test("AI Coaching", False, f"Response: {response}")
        
        # Test mood analysis
        mood_entries = [
            {"date": "2024-01-01", "mood": "Happy"},
            {"date": "2024-01-02", "mood": "Neutral"},
            {"date": "2024-01-03", "mood": "Excited"}
        ]
        ai_request = {"prompt": json.dumps(mood_entries)}
        success, response = self.run_request('POST', 'ai/analyze', ai_request)
        if success and response.get('success'):
            self.log_test("AI Mood Analysis", True, f"Generated mood analysis")
        else:
            self.log_test("AI Mood Analysis", False, f"Response: {response}")
        
        # Test general chat
        ai_request = {
            "prompt": "What are some good tips for building consistent habits?",
            "context": "User is new to habit tracking"
        }
        success, response = self.run_request('POST', 'ai/chat', ai_request)
        if success and response.get('success'):
            self.log_test("AI Chat", True, f"Generated chat response")
        else:
            self.log_test("AI Chat", False, f"Response: {response}")

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting DailyRoutine API Testing")
        print(f"🔗 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_auth_flow():
            print("❌ Authentication failed - stopping tests")
            return False
            
        # Test habits CRUD
        existing_habits = self.test_habits_crud()
        
        # Test completions
        self.test_completions(existing_habits)
        
        # Test journal CRUD
        self.test_journal_crud()
        
        # Test stats and streaks
        self.test_stats_and_streaks()
        
        # Test AI features
        self.test_ai_features()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed < self.tests_run:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    # Test with external URL first (as configured in .env)
    print("Testing with external URL (as configured in frontend/.env)")
    external_tester = DailyRoutineAPITester("https://v1-main-dailyroutine.preview.emergentagent.com")
    external_success = external_tester.run_all_tests()
    
    # Also test with localhost as suggested by main agent
    print("\n" + "="*80)
    print("Testing with localhost URL (as suggested by main agent)")
    localhost_tester = DailyRoutineAPITester("http://localhost:8001")
    localhost_success = localhost_tester.run_all_tests()
    
    print(f"\n🏁 FINAL RESULTS:")
    print(f"External URL tests: {'✅ PASSED' if external_success else '❌ FAILED'}")
    print(f"Localhost tests: {'✅ PASSED' if localhost_success else '❌ FAILED'}")
    
    return external_success or localhost_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)