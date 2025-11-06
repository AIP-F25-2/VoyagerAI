'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from './AuthModal';
import UserProfile from './UserProfile';

export default function Header() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  const handleAuthClick = (mode: 'login' | 'signup') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  if (isLoading) {
    return (
      <header className="p-4 sticky top-0 z-50 flex items-center justify-between border-b border-white/10 bg-white/70 dark:bg-black/40 backdrop-blur-md">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-wide select-none text-[#0a1042] dark:text-white">
          VOYAGERAI <span className="text-sm font-normal text-gray-500 dark:text-gray-300">Team Odyssey</span>
        </h1>
        <div className="flex items-center space-x-4">
          <div className="animate-pulse bg-white/20 h-8 w-20 rounded"></div>
        </div>
      </header>
    );
  }

  return (
    <>
      <header className="p-4 bg-black/40 backdrop-blur-md border-b border-white/10 flex items-center justify-between sticky top-0 z-50 glass-dark">
        <h1 className="text-3xl font-extrabold text-white tracking-wide select-none">
          VOYAGERAI <span className="text-sm font-normal text-gray-300">Team Odyssey</span>
        </h1>
        
        <div className="flex items-center space-x-4">
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-3">
              <span className="text-white text-sm hidden sm:block">
                Welcome, {user.name}
              </span>
              <button
                onClick={() => setProfileModalOpen(true)}
                className="flex items-center space-x-2 px-3 py-1.5 border border-black/10 dark:border-white/30 text-[#0a1042] dark:text-white rounded-xl hover:bg-black/5 dark:hover:bg-white/20 transition"
              >
                <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">
                    {user.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="hidden sm:block">Profile</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleAuthClick('login')}
                className="px-4 py-1.5 border border-black/10 dark:border-white/30 text-[#0a1042] dark:text-white rounded-xl hover:bg-black/5 dark:hover:bg-white/20 transition hover:cursor-pointer"
              >
                Sign In
              </button>
              <button
                onClick={() => handleAuthClick('signup')}
                className="px-4 py-1.5 rounded-xl text-white transition hover:cursor-pointer"
                style={{
                  background: 'linear-gradient(135deg, var(--brand-primary), #6a5cff)',
                  boxShadow: '0 8px 22px rgba(0,136,255,0.25)'
                }}
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </header>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        mode={authMode}
        onModeChange={setAuthMode}
      />

      <UserProfile
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
      />
    </>
  );
}
