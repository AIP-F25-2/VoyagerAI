"use client";

import { useState } from "react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"form" | "loading" | "success" | "error">("form");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setMessage("Email is required");
      return;
    }

    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.success) {
        setStatus("success");
        setMessage(data.message);
      } else {
        setStatus("error");
        setMessage(data.message);
      }
    } catch (error) {
      setStatus("error");
      setMessage("Failed to send reset email. Please try again.");
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white flex items-center justify-center p-8">
        <div className="max-w-md w-full bg-gray-800/50 p-8 rounded-lg text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Sending reset email...</p>
        </div>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white flex items-center justify-center p-8">
        <div className="max-w-md w-full bg-gray-800/50 p-8 rounded-lg text-center">
          <div className="text-green-500 text-6xl mb-4">✓</div>
          <p className="text-green-400 mb-6">{message}</p>
          <Link
            href="/login"
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg inline-block"
          >
            Back to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-gray-800/50 p-8 rounded-lg">
        <h1 className="text-3xl font-bold mb-6 text-center">Forgot Password</h1>
        <p className="text-gray-300 mb-6 text-center">
          Enter your email address and we'll send you a link to reset your password.
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          {message && (
            <div className={`text-sm ${status === "error" ? "text-red-400" : "text-gray-300"}`}>
              {message}
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-semibold"
          >
            Send Reset Email
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link href="/login" className="text-blue-400 hover:text-blue-300">
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
