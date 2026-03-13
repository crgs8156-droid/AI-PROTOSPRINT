import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Layout } from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, Loader2, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SENTIMENT_COLORS = {
  'Positive': '#10B981',
  'Excited': '#F59E0B',
  'Calm': '#0EA5E9',
  'Anxious': '#F97316',
  'Overwhelmed': '#EF4444',
  'Lethargic': '#6B7280',
  'Sad': '#8B5CF6',
  'Neutral': '#9CA3AF'
};

export const EmotionalDashboard = () => {
  const [dashboardData, setDashboardData] = useState([]);
  const [weeklySummary, setWeeklySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [analyzingAll, setAnalyzingAll] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const res = await axios.get(`${API}/ai/emotional-dashboard`);
      setDashboardData(res.data.data);
      
      // Also fetch weekly summary
      fetchWeeklySummary();
    } catch (error) {
      toast.error('Failed to load emotional data');
    } finally {
      setLoading(false);
    }
  };

  const fetchWeeklySummary = async () => {
    setLoadingSummary(true);
    try {
      const res = await axios.post(`${API}/ai/weekly-summary`);
      setWeeklySummary(res.data.data);
    } catch (error) {
      console.error('Failed to load weekly summary');
    } finally {
      setLoadingSummary(false);
    }
  };

  const analyzeAllEntries = async () => {
    setAnalyzingAll(true);
    toast.info('Analyzing all unanalyzed entries...');
    
    try {
      const res = await axios.post(`${API}/ai/analyze-batch`);
      const { processed, failed } = res.data.data;
      
      toast.success(`Analyzed ${processed} entries! ${failed > 0 ? `(${failed} failed)` : ''}`);
      
      // Refresh data
      await fetchDashboardData();
    } catch (error) {
      toast.error('Failed to analyze entries');
    } finally {
      setAnalyzingAll(false);
    }
  };

  // Prepare chart data
  const chartData = dashboardData
    .filter(d => d.sentiment)
    .map(d => ({
      date: new Date(d.entry_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      sentiment: d.sentiment,
      color: SENTIMENT_COLORS[d.sentiment] || SENTIMENT_COLORS['Neutral']
    }));

  // Calculate theme frequency
  const themeFrequency = {};
  dashboardData.forEach(entry => {
    if (entry.themes) {
      entry.themes.forEach(theme => {
        themeFrequency[theme] = (themeFrequency[theme] || 0) + 1;
      });
    }
  });

  const topThemes = Object.entries(themeFrequency)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  // Check if there are unanalyzed entries
  const unanalyzedCount = dashboardData.filter(d => !d.analyzed_at).length;

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
      <div className="space-y-8" data-testid="emotional-dashboard">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              🧠 Emotional Insights
            </h1>
            <p className="mt-2 text-base text-slate-600 dark:text-slate-400">
              AI-powered analysis of your emotional patterns
            </p>
          </div>
          {unanalyzedCount > 0 && (
            <Button
              onClick={analyzeAllEntries}
              disabled={analyzingAll}
              data-testid="analyze-all-button"
            >
              {analyzingAll ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <TrendingUp className="mr-2 h-4 w-4" />
                  Analyze {unanalyzedCount} Entries
                </>
              )}
            </Button>
          )}
        </div>

        {dashboardData.length === 0 ? (
          <Card className="p-12 text-center">
            <p className="text-lg text-slate-600 dark:text-slate-400">
              Start journaling to see your emotional insights!
            </p>
          </Card>
        ) : (
          <>
            {/* Sentiment Timeline */}
            <Card className="p-8">
              <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-6">
                Sentiment Timeline (Last 14 Days)
              </h2>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis hide />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload[0]) {
                          return (
                            <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700">
                              <p className="font-medium">{payload[0].payload.date}</p>
                              <p className="text-sm" style={{ color: payload[0].payload.color }}>
                                {payload[0].payload.sentiment}
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="sentiment" fill="#8884d8" radius={[8, 8, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-center text-slate-500 py-12">
                  No analyzed entries yet. Write in your journal to see insights!
                </p>
              )}
            </Card>

            {/* Theme Cloud */}
            {topThemes.length > 0 && (
              <Card className="p-8">
                <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-6">
                  Common Themes
                </h2>
                <div className="flex flex-wrap gap-3">
                  {topThemes.map(([theme, count]) => (
                    <div
                      key={theme}
                      className="px-4 py-2 bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 rounded-full border border-violet-200 dark:border-violet-800"
                      style={{
                        fontSize: `${Math.min(1.5, 0.875 + count * 0.125)}rem`,
                      }}
                    >
                      <span className="font-medium text-violet-900 dark:text-violet-300">
                        {theme}
                      </span>
                      <span className="ml-2 text-xs text-violet-600 dark:text-violet-400">
                        ({count})
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Weekly AI Summary */}
            <Card className="p-8 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border-emerald-200 dark:border-emerald-800">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100">
                  Weekly Summary
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchWeeklySummary}
                  disabled={loadingSummary}
                  data-testid="refresh-summary"
                >
                  {loadingSummary ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {loadingSummary ? (
                <div className="space-y-2">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse w-5/6" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse w-4/6" />
                </div>
              ) : weeklySummary ? (
                <div>
                  {weeklySummary.date_range && (
                    <p className="text-sm text-emerald-700 dark:text-emerald-400 mb-3">
                      {weeklySummary.date_range} • {weeklySummary.entries_count} entries
                    </p>
                  )}
                  <p className="text-base leading-relaxed text-slate-800 dark:text-slate-200">
                    {weeklySummary.summary}
                  </p>
                </div>
              ) : (
                <p className="text-slate-600 dark:text-slate-400">
                  No summary available yet
                </p>
              )}
            </Card>

            {/* Mood Calendar */}
            <Card className="p-8">
              <h2 className="font-heading text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-6">
                14-Day Mood Calendar
              </h2>
              <div className="grid grid-cols-7 gap-3">
                {dashboardData.slice(-14).map((entry, idx) => {
                  const entryDate = new Date(entry.entry_date);
                  const sentiment = entry.sentiment || 'Neutral';
                  const bgColor = SENTIMENT_COLORS[sentiment];
                  
                  return (
                    <div
                      key={idx}
                      className="aspect-square rounded-xl p-3 cursor-pointer hover:scale-105 transition-transform"
                      style={{
                        backgroundColor: entry.sentiment ? `${bgColor}20` : '#f3f4f6',
                        border: `2px solid ${entry.sentiment ? bgColor : '#e5e7eb'}`,
                      }}
                      title={`${entry.entry_date}: ${sentiment}`}
                    >
                      <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                        {entryDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>
                      {entry.sentiment ? (
                        <div
                          className="text-xs font-bold mt-1"
                          style={{ color: bgColor }}
                        >
                          {sentiment}
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400 mt-1">
                          Not analyzed
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
};
