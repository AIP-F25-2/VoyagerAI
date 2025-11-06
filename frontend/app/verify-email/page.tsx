"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided");
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch("/api/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
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
        setMessage("Failed to verify email. Please try again.");
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-gray-800/50 p-8 rounded-lg">
        <h1 className="text-3xl font-bold mb-6 text-center">Email Verification</h1>
        
        {status === "loading" && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p>Verifying your email...</p>
          </div>
        )}

        {status === "success" && (
          <div className="text-center">
            <div className="text-green-500 text-6xl mb-4">✓</div>
            <p className="text-green-400 mb-6">{message}</p>
            <a
              href="/login"
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg inline-block"
            >
              Go to Login
            </a>
          </div>
        )}

        {status === "error" && (
          <div className="text-center">
            <div className="text-red-500 text-6xl mb-4">✗</div>
            <p className="text-red-400 mb-6">{message}</p>
            <div className="space-y-2">
              <a
                href="/login"
                className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg inline-block mr-2"
              >
                Go to Login
              </a>
              <a
                href="/signup"
                className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg inline-block"
              >
                Sign Up Again
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
