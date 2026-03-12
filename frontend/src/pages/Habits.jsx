import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Layout } from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Edit2, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EMOJI_OPTIONS = ['📚', '🧘', '💪', '💧', '🛌', '🏃', '🎨', '🎸', '🍎', '🧠', '✍️', '☕'];
const COLOR_OPTIONS = ['#7C3AED', '#0EA5E9', '#10B981', '#F59E0B', '#EC4899', '#EF4444', '#06B6D4', '#8B5CF6'];

export const Habits = () => {
  const [habits, setHabits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingHabit, setEditingHabit] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    emoji: '📚',
    color: '#10B981',
  });

  useEffect(() => {
    fetchHabits();
  }, []);

  const fetchHabits = async () => {
    try {
      const res = await axios.get(`${API}/habits`);
      setHabits(res.data.data);
    } catch (error) {
      toast.error('Failed to load habits');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingHabit) {
        await axios.put(`${API}/habits/${editingHabit.id}`, formData);
        toast.success('Habit updated!');
      } else {
        await axios.post(`${API}/habits`, formData);
        toast.success('Habit created!');
      }
      fetchHabits();
      setDialogOpen(false);
      resetForm();
    } catch (error) {
      toast.error('Failed to save habit');
    }
  };

  const handleEdit = (habit) => {
    setEditingHabit(habit);
    setFormData({
      name: habit.name,
      emoji: habit.emoji,
      color: habit.color,
    });
    setDialogOpen(true);
  };

  const handleDelete = async (habitId) => {
    if (!window.confirm('Are you sure you want to delete this habit?')) return;
    try {
      await axios.delete(`${API}/habits/${habitId}`);
      toast.success('Habit deleted');
      fetchHabits();
    } catch (error) {
      toast.error('Failed to delete habit');
    }
  };

  const handleToggle = async (habit) => {
    try {
      await axios.patch(`${API}/habits/${habit.id}/toggle`);
      toast.success(habit.is_active ? 'Habit deactivated' : 'Habit activated');
      fetchHabits();
    } catch (error) {
      toast.error('Failed to toggle habit');
    }
  };

  const resetForm = () => {
    setEditingHabit(null);
    setFormData({ name: '', emoji: '📚', color: '#10B981' });
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
      <div className="space-y-8" data-testid="habits-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              Your Habits
            </h1>
            <p className="mt-2 text-base text-slate-600 dark:text-slate-400">
              Manage and track your daily routines
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button
                size="lg"
                data-testid="create-habit-button"
                className="h-12"
              >
                <Plus className="mr-2 h-5 w-5" />
                New Habit
              </Button>
            </DialogTrigger>
            <DialogContent data-testid="habit-dialog">
              <DialogHeader>
                <DialogTitle>{editingHabit ? 'Edit Habit' : 'Create New Habit'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="name">Habit Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Read 20 pages"
                    required
                    data-testid="habit-name-input"
                  />
                </div>
                <div>
                  <Label>Choose Emoji</Label>
                  <div className="grid grid-cols-6 gap-2 mt-2">
                    {EMOJI_OPTIONS.map((emoji) => (
                      <button
                        key={emoji}
                        type="button"
                        onClick={() => setFormData({ ...formData, emoji })}
                        className={`p-3 text-2xl rounded-xl border-2 transition-all hover:scale-110 ${
                          formData.emoji === emoji
                            ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                            : 'border-slate-200 dark:border-slate-800'
                        }`}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label>Choose Color</Label>
                  <div className="grid grid-cols-4 gap-2 mt-2">
                    {COLOR_OPTIONS.map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setFormData({ ...formData, color })}
                        className={`h-12 rounded-xl border-2 transition-all hover:scale-110 ${
                          formData.color === color
                            ? 'border-slate-900 dark:border-slate-100'
                            : 'border-transparent'
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
                <Button type="submit" className="w-full" data-testid="habit-submit-button">
                  {editingHabit ? 'Update Habit' : 'Create Habit'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Habits Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {habits.map((habit, idx) => (
            <motion.div
              key={habit.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card className={`p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300 ${
                !habit.is_active ? 'opacity-60' : ''
              }`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-4xl">{habit.emoji}</span>
                    <div>
                      <h3 className="font-heading font-semibold text-lg text-slate-900 dark:text-slate-100">
                        {habit.name}
                      </h3>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {habit.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: habit.color }}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(habit)}
                    data-testid={`toggle-habit-${habit.id}`}
                  >
                    {habit.is_active ? (
                      <ToggleRight className="h-4 w-4 mr-1" />
                    ) : (
                      <ToggleLeft className="h-4 w-4 mr-1" />
                    )}
                    {habit.is_active ? 'Active' : 'Inactive'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(habit)}
                    data-testid={`edit-habit-${habit.id}`}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(habit.id)}
                    data-testid={`delete-habit-${habit.id}`}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        {habits.length === 0 && (
          <Card className="p-12 text-center">
            <p className="text-lg text-slate-600 dark:text-slate-400">
              No habits yet. Create your first habit to get started!
            </p>
          </Card>
        )}
      </div>
    </Layout>
  );
};
