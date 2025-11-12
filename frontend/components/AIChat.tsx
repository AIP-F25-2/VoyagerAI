"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/apiClient";
import styles from "./AIChat.module.css";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface AIChatProps {
  onClose?: () => void;
  initialMessage?: string;
}

export default function AIChat({ onClose, initialMessage }: AIChatProps) {
  const { user, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(initialMessage || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialMessage) {
      handleSend(initialMessage);
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}-${Math.random()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // Prepare conversation history
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const data = await apiClient.post('/api/llm/chat', {
        message: text,
        email: user?.email || null,
        history: history,
      });

      if (data.success) {
        const assistantMessage: Message = {
          role: "assistant",
          content: data.message,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        setError(data.error || "Failed to get response");
        const errorMessage: Message = {
          role: "assistant",
          content: `Sorry, I encountered an error: ${data.error || "Unknown error"}. Please make sure OPENAI_API_KEY is configured.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Network error";
      setError(errorMsg);
      const errorMessage: Message = {
        role: "assistant",
        content: `Sorry, I couldn't connect to the AI service. ${errorMsg}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickQuestions = [
    "What events are happening this weekend?",
    "Recommend some music events",
    "Help me plan a trip to Toronto",
    "What are the best hotels in Berlin?",
  ];

  return (
    <div className={styles.chatContainer}>
      <div className={styles.chatHeader}>
        <div className={styles.headerContent}>
          <h3>🤖 VoyagerAI Assistant</h3>
          {onClose && (
            <button onClick={onClose} className={styles.closeButton}>
              ✕
            </button>
          )}
        </div>
        {!isAuthenticated && (
          <p className={styles.authNotice}>
            Sign in for personalized recommendations
          </p>
        )}
      </div>

      <div className={styles.messagesContainer}>
        {messages.length === 0 && (
          <div className={styles.welcomeMessage}>
            <p>👋 Hi! I'm your travel assistant. How can I help you today?</p>
            <div className={styles.quickQuestions}>
              <p>Try asking:</p>
              {quickQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className={styles.quickQuestionButton}
                  disabled={loading}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id || `${msg.role}-${msg.timestamp.getTime()}-${Math.random()}`}
            className={`${styles.message} ${
              msg.role === "user" ? styles.userMessage : styles.assistantMessage
            }`}
          >
            <div className={styles.messageContent}>
              <div className={styles.messageText}>{msg.content}</div>
              <div className={styles.messageTime}>
                {msg.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className={`${styles.message} ${styles.assistantMessage}`}>
            <div className={styles.messageContent}>
              <div className={styles.typingIndicator}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className={styles.errorMessage}>
          ⚠️ {error}
        </div>
      )}

      <div className={styles.inputContainer}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about events, hotels, or travel..."
          className={styles.input}
          disabled={loading}
        />
        <button
          onClick={() => handleSend()}
          className={styles.sendButton}
          disabled={loading || !input.trim()}
        >
          {loading ? "..." : "→"}
        </button>
      </div>
    </div>
  );
}

