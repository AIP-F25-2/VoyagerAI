'use client'

import Link from 'next/link'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 py-3 border-b border-white/10 glass-dark">
      <Link href="/" className="text-2xl sm:text-3xl font-extrabold tracking-wide select-none text-white hover:text-gray-200 transition">
        VOYAGERAI <span className="text-sm font-normal text-gray-300">Team Odyssey</span>
      </Link>

      <div className="flex items-center space-x-2">
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
      </div>
    </header>
  );
}
