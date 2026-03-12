import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Layout } from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Flame, Trophy, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Stats = () => {
  const [streaks, setStreaks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [streaksRes, summaryRes] = await Promise.all([
        axios.get(`${API}/stats/streaks`),
        axios.get(`${API}/stats/summary`),
      ]);
      setStreaks(streaksRes.data.data);
      setSummary(summaryRes.data.data);
    } catch (error) {
      toast.error('Failed to load stats');
    } finally {
      setLoading(false);
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
      <div className="space-y-8" data-testid="stats-page">
        {/* Header */}
        <div>
          <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Your Statistics
          </h1>
          <p className="mt-2 text-base text-slate-600 dark:text-slate-400">
            Track your progress and celebrate your achievements
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border-emerald-200 dark:border-emerald-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-emerald-100 dark:bg-emerald-900/40 rounded-xl">
                <Trophy className="h-6 w-6 text-emerald-600 dark:text-emerald-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-emerald-700 dark:text-emerald-400">Active Habits</p>
                <p className="text-3xl font-bold font-heading text-emerald-900 dark:text-emerald-50">
                  {summary?.active_habits || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border-amber-200 dark:border-amber-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-amber-100 dark:bg-amber-900/40 rounded-xl">
                <Flame className="h-6 w-6 text-amber-600 dark:text-amber-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-amber-700 dark:text-amber-400">Best Streak</p>
                <p className="text-3xl font-bold font-heading text-amber-900 dark:text-amber-50">
                  {summary?.best_streak || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 border-violet-200 dark:border-violet-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-violet-100 dark:bg-violet-900/40 rounded-xl">
                <Calendar className="h-6 w-6 text-violet-600 dark:text-violet-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-violet-700 dark:text-violet-400">Total Completions</p>
                <p className="text-3xl font-bold font-heading text-violet-900 dark:text-violet-50">
                  {summary?.total_completions || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-br from-sky-50 to-blue-50 dark:from-sky-900/20 dark:to-blue-900/20 border-sky-200 dark:border-sky-800">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-sky-100 dark:bg-sky-900/40 rounded-xl">
                <Trophy className="h-6 w-6 text-sky-600 dark:text-sky-400" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-sky-700 dark:text-sky-400">Journal Entries</p>
                <p className="text-3xl font-bold font-heading text-sky-900 dark:text-sky-50">
                  {summary?.journal_entries || 0}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Streaks */}
        <div>
          <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-6">
            Habit Streaks
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {streaks.map((streak, idx) => (
              <motion.div
                key={streak.habit_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Card className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
                  <h3 className="font-heading font-semibold text-lg text-slate-900 dark:text-slate-100 mb-4">
                    {streak.habit_name}
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
                      <div className="flex items-center space-x-2">
                        <Flame className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                        <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                          Current Streak
                        </span>
                      </div>
                      <span className="text-2xl font-bold font-heading text-amber-900 dark:text-amber-50">
                        {streak.current_streak}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
                      <div className="flex items-center space-x-2">
                        <Trophy className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                        <span className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
                          Longest Streak
                        </span>
                      </div>
                      <span className="text-2xl font-bold font-heading text-emerald-900 dark:text-emerald-50">
                        {streak.longest_streak}
                      </span>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {streaks.length === 0 && (
          <Card className="p-12 text-center">
            <p className="text-lg text-slate-600 dark:text-slate-400">
              No streak data yet. Start completing habits to build your streaks!
            </p>
          </Card>
        )}
      </div>
    </Layout>
  );
};
