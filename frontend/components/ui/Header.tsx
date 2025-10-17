'use client'

import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'

export default function Header() {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 py-3 border-b border-white/10 glass-dark">
      <Link href="/" className="text-2xl sm:text-3xl font-extrabold tracking-wide select-none text-white hover:text-gray-200 transition">
        VOYAGERAI <span className="text-sm font-normal text-gray-300">Team Odyssey</span>
      </Link>

      <div className="flex items-center space-x-2">
        {isAuthenticated ? (
          <>
            <Link 
              href="/travel-plans"
              className="px-4 py-1.5 border border-white/30 text-white rounded-xl hover:bg-white/20 transition hover:cursor-pointer"
            >
              🗺️ Travel Plans
            </Link>
            <Link 
              href="/profile"
              className="px-4 py-1.5 border border-white/30 text-white rounded-xl hover:bg-white/20 transition hover:cursor-pointer"
            >
              👤 {user?.name}
            </Link>
            <button
              onClick={logout}
              className="px-4 py-1.5 rounded-xl text-white transition hover:cursor-pointer bg-red-600 hover:bg-red-700"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link 
              href="/login"
              className="px-4 py-1.5 border border-white/30 text-white rounded-xl hover:bg-white/20 transition hover:cursor-pointer"
            >
              Sign In
            </Link>
            <Link 
              href="/signup"
              className="px-4 py-1.5 rounded-xl text-white transition hover:cursor-pointer"
              style={{
                background: 'linear-gradient(135deg, #0088ff, #6a5cff)',
                boxShadow: '0 8px 22px rgba(0,136,255,0.25)'
              }}
            >
              Sign Up
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
