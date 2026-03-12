import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Layout } from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Flame, TrendingUp, BookOpen, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Dashboard = () => {
  const [habits, setHabits] = useState([]);
  const [todayCompletions, setTodayCompletions] = useState([]);
  const [stats, setStats] = useState(null);
  const [recentJournals, setRecentJournals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [habitsRes, completionsRes, statsRes, journalsRes] = await Promise.all([
        axios.get(`${API}/habits`),
        axios.get(`${API}/completions/today`),
        axios.get(`${API}/stats/summary`),
        axios.get(`${API}/journal?limit=3`),
      ]);

      setHabits(habitsRes.data.data.filter(h => h.is_active));
      setTodayCompletions(completionsRes.data.data);
      setStats(statsRes.data.data);
      setRecentJournals(journalsRes.data.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const isHabitCompleted = (habitId) => {
    return todayCompletions.some(c => c.habit_id === habitId);
  };

  const toggleHabitCompletion = async (habitId) => {
    const isCompleted = isHabitCompleted(habitId);

    try {
      if (isCompleted) {
        await axios.delete(`${API}/completions/${habitId}/today`);
        setTodayCompletions(prev => prev.filter(c => c.habit_id !== habitId));
      } else {
        const res = await axios.post(`${API}/completions`, { habit_id: habitId });
        setTodayCompletions(prev => [...prev, res.data.data]);
        toast.success('Great job! Keep the streak going!');
      }
    } catch (error) {
      toast.error('Failed to update habit');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="dashboard">
        {/* Header */}
        <div>
          <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Today's Overview
          </h1>
          <p className="mt-2 text-base text-slate-600 dark:text-slate-400">
            Keep building those habits, one day at a time
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {/* Hero Tile - Today's Habits */}
          <Card className="col-span-1 md:col-span-4 lg:col-span-4 row-span-2 p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100">
                Today's Habits
              </h2>
              <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                {todayCompletions.length} / {habits.length} completed
              </span>
            </div>
            <div className="space-y-4">
              {habits.map((habit, idx) => (
                <motion.div
                  key={habit.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-center space-x-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                  data-testid={`habit-item-${habit.id}`}
                >
                  <Checkbox
                    checked={isHabitCompleted(habit.id)}
                    onCheckedChange={() => toggleHabitCompletion(habit.id)}
                    data-testid={`habit-checkbox-${habit.id}`}
                    className="h-6 w-6"
                  />
                  <div className="flex items-center flex-1 space-x-3">
                    <span className="text-2xl">{habit.emoji}</span>
                    <span className="font-medium text-slate-900 dark:text-slate-100">
                      {habit.name}
                    </span>
                  </div>
                  <div
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: habit.color }}
                  />
                </motion.div>
              ))}
            </div>
          </Card>

          {/* Stat Tiles */}
          <Card className="col-span-1 md:col-span-2 lg:col-span-2 p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
                <Flame className="h-6 w-6 text-amber-600 dark:text-amber-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Best Streak</p>
                <p className="text-3xl font-bold font-heading text-slate-900 dark:text-slate-50">
                  {stats?.best_streak || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="col-span-1 md:col-span-2 lg:col-span-2 p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
                <CheckCircle2 className="h-6 w-6 text-emerald-600 dark:text-emerald-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Total Completions</p>
                <p className="text-3xl font-bold font-heading text-slate-900 dark:text-slate-50">
                  {stats?.total_completions || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="col-span-1 md:col-span-2 lg:col-span-2 p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-violet-50 dark:bg-violet-900/20 rounded-xl">
                <BookOpen className="h-6 w-6 text-violet-600 dark:text-violet-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Journal Entries</p>
                <p className="text-3xl font-bold font-heading text-slate-900 dark:text-slate-50">
                  {stats?.journal_entries || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="col-span-1 md:col-span-2 lg:col-span-2 p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-sky-50 dark:bg-sky-900/20 rounded-xl">
                <TrendingUp className="h-6 w-6 text-sky-600 dark:text-sky-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Active Habits</p>
                <p className="text-3xl font-bold font-heading text-slate-900 dark:text-slate-50">
                  {stats?.active_habits || 0}
                </p>
              </div>
            </div>
          </Card>

          {/* Recent Journal */}
          <Card className="col-span-1 md:col-span-4 lg:col-span-6 p-8 bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 border border-violet-200 dark:border-violet-800">
            <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-4">
              Recent Journal Entries
            </h2>
            {recentJournals.length > 0 ? (
              <div className="space-y-3">
                {recentJournals.map((entry) => (
                  <div
                    key={entry.id}
                    className="p-4 bg-white/60 dark:bg-slate-900/60 backdrop-blur-sm rounded-xl border border-violet-200/50 dark:border-violet-800/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-violet-700 dark:text-violet-400">
                        {entry.mood}
                      </span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {entry.entry_date}
                      </span>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
                      {entry.content}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-600 dark:text-slate-400">No journal entries yet. Start writing!</p>
            )}
          </Card>
        </div>
      </div>
    </Layout>
  );
};
