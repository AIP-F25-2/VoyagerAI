'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, login, signup, getProfile, verifyToken } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  signup: (name: string, email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('voyagerai_token');
    if (storedToken) {
      verifyStoredToken(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const verifyStoredToken = async (storedToken: string) => {
    try {
      const response = await verifyToken(storedToken);
      if (response.success && response.user) {
        setToken(storedToken);
        setUser(response.user);
      } else {
        // Token is invalid, remove it
        localStorage.removeItem('voyagerai_token');
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      localStorage.removeItem('voyagerai_token');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (email: string, password: string) => {
    try {
      const response = await login(email, password);
      if (response.success && response.token && response.user) {
        setToken(response.token);
        setUser(response.user);
        localStorage.setItem('voyagerai_token', response.token);
        return { success: true };
      } else {
        return { success: false, message: response.message || 'Login failed' };
      }
    } catch (error) {
      return { success: false, message: 'Network error' };
    }
  };

  const handleSignup = async (name: string, email: string, password: string) => {
    try {
      const response = await signup(name, email, password);
      if (response.success && response.token && response.user) {
        setToken(response.token);
        setUser(response.user);
        localStorage.setItem('voyagerai_token', response.token);
        return { success: true };
      } else {
        return { success: false, message: response.message || 'Signup failed' };
      }
    } catch (error) {
      return { success: false, message: 'Network error' };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('voyagerai_token');
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    login: handleLogin,
    signup: handleSignup,
    logout,
    isAuthenticated: !!user && !!token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
