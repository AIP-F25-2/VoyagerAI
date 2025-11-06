'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from './AuthModal';
import UserProfile from './UserProfile';

export default function Header() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const pathname = usePathname();

  const handleAuthClick = (mode: 'login' | 'signup') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  if (isLoading) {
    return (
      <header className="p-4 bg-black/40 backdrop-blur-md border-b border-white/10 flex items-center justify-between sticky top-0 z-50 glass-dark">
        <h1 className="text-3xl font-extrabold text-white tracking-wide select-none">
          VOYAGERAI <span className="text-sm font-normal text-gray-300">Team Odyssey</span>
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
        <div className="flex items-center space-x-8">
          <h1 className="text-3xl font-extrabold text-white tracking-wide select-none">
            VOYAGERAI <span className="text-sm font-normal text-gray-300">Team Odyssey</span>
          </h1>
          
          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link
              href="/"
              className={`px-3 py-2 rounded-lg transition ${
                pathname === "/"
                  ? "bg-blue-600/30 text-blue-300"
                  : "text-gray-300 hover:text-white hover:bg-white/10"
              }`}
            >
              🎟️ Events
            </Link>
            <Link
              href="/hotels"
              className={`px-3 py-2 rounded-lg transition ${
                pathname === "/hotels"
                  ? "bg-blue-600/30 text-blue-300"
                  : "text-gray-300 hover:text-white hover:bg-white/10"
              }`}
            >
              🏨 Hotels
            </Link>
            <Link
              href="/travel-plans"
              className={`px-3 py-2 rounded-lg transition ${
                pathname === "/travel-plans"
                  ? "bg-blue-600/30 text-blue-300"
                  : "text-gray-300 hover:text-white hover:bg-white/10"
              }`}
            >
              📋 Travel Plans
            </Link>
          </nav>
        </div>
        
        <div className="flex items-center space-x-4">
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-3">
              <span className="text-white text-sm hidden sm:block">
                Welcome, {user.name}
              </span>
              <button
                onClick={() => setProfileModalOpen(true)}
                className="flex items-center space-x-2 px-3 py-1.5 border border-white/30 text-white rounded-lg hover:bg-white/20 transition"
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
                className="px-4 py-1.5 border border-white/30 text-white rounded-lg hover:bg-white/20 transition hover:cursor-pointer"
              >
                Sign In
              </button>
              <button
                onClick={() => handleAuthClick('signup')}
                className="px-4 py-1.5 border border-white/30 text-white rounded-lg hover:bg-blue-600/60 transition hover:cursor-pointer"
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
