import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Home, BookOpen, CheckCircle2, BarChart2, Sparkles, LogOut, Users, Settings as SettingsIcon, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/habits', icon: CheckCircle2, label: 'Habits' },
    { to: '/journal', icon: BookOpen, label: 'Journal' },
    { to: '/insights', icon: Brain, label: 'Insights' },
    { to: '/stats', icon: BarChart2, label: 'Stats' },
    { to: '/friends', icon: Users, label: 'Friends' },
    { to: '/ai-assistant', icon: Sparkles, label: 'AI Assistant' },
    { to: '/settings', icon: SettingsIcon, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Glassmorphic Nav */}
      <nav className="sticky top-0 z-50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="font-heading text-2xl font-bold text-slate-900 dark:text-slate-50">
                DailyRoutine
              </h1>
              <div className="hidden md:flex space-x-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
                    className={({ isActive }) =>
                      `flex items-center space-x-2 px-4 py-2 rounded-xl font-medium transition-all ${isActive
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400'
                        : 'text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800'
                      }`
                    }
                  >
                    <item.icon className="h-5 w-5" strokeWidth={1.5} />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {user?.name}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                data-testid="logout-button"
                className="hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};
