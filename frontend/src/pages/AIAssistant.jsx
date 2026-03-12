import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Sparkles, Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AIAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState('');

  useEffect(() => {
    fetchContext();
    setMessages([
      {
        role: 'assistant',
        content: 'Hello! I\'m your AI habit coach. I can help you with:\n\n• Analyzing your habit patterns\n• Providing motivational insights\n• Suggesting improvements\n• Answering questions about personal growth\n\nHow can I assist you today?',
      },
    ]);
  }, []);

  const fetchContext = async () => {
    try {
      const [habitsRes, statsRes] = await Promise.all([
        axios.get(`${API}/habits`),
        axios.get(`${API}/stats/summary`),
      ]);
      const contextStr = `User has ${statsRes.data.data.active_habits} active habits with ${statsRes.data.data.total_completions} total completions and a best streak of ${statsRes.data.data.best_streak} days.`;
      setContext(contextStr);
    } catch (error) {
      console.error('Failed to fetch context:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API}/ai/chat`, {
        prompt: input,
        context: context,
      });

      const aiMessage = { role: 'assistant', content: res.data.data };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      toast.error('Failed to get response');
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6" data-testid="ai-assistant-page">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center p-4 bg-gradient-to-br from-violet-100 to-purple-100 dark:from-violet-900/40 dark:to-purple-900/40 rounded-2xl mb-4">
            <Sparkles className="h-8 w-8 text-violet-600 dark:text-violet-400" strokeWidth={1.5} />
          </div>
          <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            AI Assistant
          </h1>
          <p className="mt-2 text-base text-slate-600 dark:text-slate-400">
            Your personal habit coach powered by AI
          </p>
        </div>

        {/* Chat Container */}
        <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg">
          <div className="h-[600px] flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-emerald-500 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </motion.div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-100 dark:bg-slate-800 p-4 rounded-2xl">
                    <Loader2 className="h-5 w-5 animate-spin text-violet-600 dark:text-violet-400" />
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-slate-200 dark:border-slate-800 p-4">
              <div className="flex space-x-2">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your habits..."
                  rows={2}
                  disabled={loading}
                  data-testid="ai-chat-input"
                  className="resize-none"
                />
                <Button
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  data-testid="ai-send-button"
                  size="lg"
                  className="h-auto"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button
            variant="outline"
            onClick={() => setInput('Analyze my habit patterns and give me insights')}
            className="h-auto p-4 justify-start text-left"
          >
            <Sparkles className="h-5 w-5 mr-3 text-violet-600" />
            <div>
              <p className="font-medium">Analyze My Habits</p>
              <p className="text-xs text-slate-500">Get insights on your progress</p>
            </div>
          </Button>
          <Button
            variant="outline"
            onClick={() => setInput('Give me motivation to keep going with my habits')}
            className="h-auto p-4 justify-start text-left"
          >
            <Sparkles className="h-5 w-5 mr-3 text-emerald-600" />
            <div>
              <p className="font-medium">Get Motivated</p>
              <p className="text-xs text-slate-500">Boost your motivation</p>
            </div>
          </Button>
        </div>
      </div>
    </Layout>
  );
};
