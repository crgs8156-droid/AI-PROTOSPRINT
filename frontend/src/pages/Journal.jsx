import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Layout } from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Edit2, Trash2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MOODS = [
  { value: 'Happy', emoji: '😊', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' },
  { value: 'Energized', emoji: '⚡', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400' },
  { value: 'Neutral', emoji: '😐', color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400' },
  { value: 'Sad', emoji: '😢', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' },
  { value: 'Anxious', emoji: '😰', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400' },
];

export const Journal = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summary, setSummary] = useState('');
  const [formData, setFormData] = useState({
    content: '',
    mood: 'Happy',
  });

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    try {
      const res = await axios.get(`${API}/journal`);
      setEntries(res.data.data);
    } catch (error) {
      toast.error('Failed to load journal entries');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingEntry) {
        await axios.put(`${API}/journal/${editingEntry.id}`, formData);
        toast.success('Entry updated!');
      } else {
        await axios.post(`${API}/journal`, formData);
        toast.success('Entry created!');
      }
      fetchEntries();
      setDialogOpen(false);
      resetForm();
      setSummary('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save entry');
    }
  };

  const handleEdit = (entry) => {
    setEditingEntry(entry);
    setFormData({
      content: entry.content,
      mood: entry.mood,
    });
    setDialogOpen(true);
  };

  const handleDelete = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this entry?')) return;
    try {
      await axios.delete(`${API}/journal/${entryId}`);
      toast.success('Entry deleted');
      fetchEntries();
    } catch (error) {
      toast.error('Failed to delete entry');
    }
  };

  const handleSummarize = async () => {
    if (!formData.content.trim()) {
      toast.error('Please write something first');
      return;
    }
    setSummarizing(true);
    try {
      const res = await axios.post(`${API}/ai/summarize`, {
        prompt: formData.content,
      });
      setSummary(res.data.data);
      toast.success('Summary generated!');
    } catch (error) {
      toast.error('Failed to generate summary');
    } finally {
      setSummarizing(false);
    }
  };

  const resetForm = () => {
    setEditingEntry(null);
    setFormData({ content: '', mood: 'Happy' });
  };

  const getMoodStyle = (mood) => {
    return MOODS.find(m => m.value === mood) || MOODS[0];
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
      <div className="space-y-8" data-testid="journal-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              Journal
            </h1>
            <p className="mt-2 text-base text-slate-600 dark:text-slate-400">
              Reflect on your journey and track your growth
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) {
              resetForm();
              setSummary('');
            }
          }}>
            <DialogTrigger asChild>
              <Button
                size="lg"
                data-testid="create-entry-button"
                className="h-12"
              >
                <Plus className="mr-2 h-5 w-5" />
                New Entry
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="journal-dialog">
              <DialogHeader>
                <DialogTitle>{editingEntry ? 'Edit Entry' : 'New Journal Entry'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label>How are you feeling?</Label>
                  <div className="grid grid-cols-5 gap-2 mt-2">
                    {MOODS.map((mood) => (
                      <button
                        key={mood.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, mood: mood.value })}
                        className={`p-4 rounded-xl border-2 transition-all hover:scale-105 ${
                          formData.mood === mood.value
                            ? 'border-emerald-500 ' + mood.color
                            : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50'
                        }`}
                      >
                        <div className="text-2xl mb-1">{mood.emoji}</div>
                        <div className="text-xs font-medium">{mood.value}</div>
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label htmlFor="content">Your thoughts</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleSummarize}
                      disabled={summarizing}
                      data-testid="summarize-button"
                    >
                      <Sparkles className="mr-1 h-4 w-4" />
                      {summarizing ? 'Summarizing...' : 'AI Summary'}
                    </Button>
                  </div>
                  <Textarea
                    id="content"
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    placeholder="What's on your mind today?"
                    required
                    rows={10}
                    data-testid="journal-content-input"
                    className="font-journal text-lg leading-loose"
                  />
                </div>
                {summary && (
                  <div className="p-4 bg-violet-50 dark:bg-violet-900/20 rounded-xl border border-violet-200 dark:border-violet-800">
                    <p className="text-sm font-medium text-violet-900 dark:text-violet-300 mb-2">
                      AI Summary:
                    </p>
                    <p className="text-sm text-violet-700 dark:text-violet-400">
                      {summary}
                    </p>
                  </div>
                )}
                <Button type="submit" className="w-full" data-testid="journal-submit-button">
                  {editingEntry ? 'Update Entry' : 'Save Entry'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Entries List */}
        <div className="space-y-6">
          {entries.map((entry, idx) => {
            const moodStyle = getMoodStyle(entry.mood);
            const sentimentColors = {
              'Positive': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400 border-emerald-300',
              'Excited': 'bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400 border-amber-300',
              'Calm': 'bg-sky-100 text-sky-700 dark:bg-sky-900/20 dark:text-sky-400 border-sky-300',
              'Anxious': 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400 border-orange-300',
              'Overwhelmed': 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400 border-red-300',
              'Lethargic': 'bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400 border-gray-300',
              'Sad': 'bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400 border-purple-300',
            };
            
            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Card className="p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex flex-col space-y-2">
                      <div className="flex items-center space-x-3">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${moodStyle.color}`}>
                          {moodStyle.emoji} {entry.mood}
                        </span>
                        {entry.sentiment ? (
                          <span className={`px-3 py-1 rounded-full text-sm font-medium border ${sentimentColors[entry.sentiment] || sentimentColors['Calm']}`}>
                            ✨ {entry.sentiment}
                          </span>
                        ) : entry.analyzed_at === undefined ? (
                          <span className="px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                            🔄 Analyzing...
                          </span>
                        ) : null}
                        <span className="text-sm text-slate-500 dark:text-slate-400">
                          {entry.entry_date}
                        </span>
                      </div>
                      {entry.themes && entry.themes.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {entry.themes.map((theme, i) => (
                            <span
                              key={i}
                              className="px-2 py-1 text-xs rounded-md bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                            >
                              {theme}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(entry)}
                        data-testid={`edit-entry-${entry.id}`}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(entry.id)}
                        data-testid={`delete-entry-${entry.id}`}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <p className="font-journal text-lg leading-loose text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
                    {entry.content}
                  </p>
                  {entry.ai_summary && (
                    <div className="mt-4 p-4 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800">
                      <p className="text-sm font-medium text-violet-900 dark:text-violet-300 mb-1">
                        AI Insight:
                      </p>
                      <p className="text-sm text-violet-700 dark:text-violet-400">
                        {entry.ai_summary}
                      </p>
                    </div>
                  )}
                </Card>
              </motion.div>
            );
          })}
        </div>

        {entries.length === 0 && (
          <Card className="p-12 text-center">
            <img
              src="https://images.unsplash.com/photo-1589221475596-7133b597dc21?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHwzfHxjYWxtJTIwbW9ybmluZyUyMGNvZmZlZSUyMGpvdXJuYWx8ZW58MHx8fHwxNzczMzU0MjA3fDA&ixlib=rb-4.1.0&q=85"
              alt="Empty journal"
              className="w-64 h-64 mx-auto object-cover rounded-2xl mb-6 opacity-60"
            />
            <p className="text-lg text-slate-600 dark:text-slate-400">
              No journal entries yet. Start writing to track your thoughts and feelings!
            </p>
          </Card>
        )}
      </div>
    </Layout>
  );
};
