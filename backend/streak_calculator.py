from datetime import date, timedelta
from typing import List


def calculate_streaks(completion_dates: List[date]) -> dict:
    """
    Calculate current and longest streak from a list of completion dates.
    
    Args:
        completion_dates: List of date objects when habit was completed
    
    Returns:
        dict with 'current_streak' and 'longest_streak'
    """
    if not completion_dates:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Sort dates in ascending order
    sorted_dates = sorted(completion_dates)
    
    # Calculate current streak (consecutive days up to today or yesterday)
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    current_streak = 0
    if sorted_dates[-1] == today or sorted_dates[-1] == yesterday:
        current_streak = 1
        check_date = sorted_dates[-1] - timedelta(days=1)
        
        for i in range(len(sorted_dates) - 2, -1, -1):
            if sorted_dates[i] == check_date:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
    
    # Calculate longest streak
    longest_streak = 1
    temp_streak = 1
    
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i-1] + timedelta(days=1):
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        elif sorted_dates[i] != sorted_dates[i-1]:
            temp_streak = 1
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }
