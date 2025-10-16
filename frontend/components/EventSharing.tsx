"use client";

import { useState } from "react";

interface EventSharingProps {
  event: {
    title: string;
    venue?: string;
    city?: string;
    date?: string;
    url?: string;
  };
  userEmail?: string;
}

export default function EventSharing({ event, userEmail }: EventSharingProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSharing, setIsSharing] = useState(false);

  const shareEvent = async (platform: string) => {
    setIsSharing(true);
    
    try {
      const response = await fetch("http://localhost:5000/api/events/share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: userEmail,
          title: event.title,
          venue: event.venue,
          city: event.city,
          date: event.date,
          url: event.url,
          platform: platform
        })
      });

      const data = await response.json();
      
      if (data.success && data.share_urls[platform]) {
        // Open the share URL
        window.open(data.share_urls[platform], '_blank', 'width=600,height=400');
      } else {
        alert("Failed to share event");
      }
    } catch (error) {
      console.error("Share error:", error);
      alert("Failed to share event");
    } finally {
      setIsSharing(false);
    }
  };

  const shareOptions = [
    { id: "facebook", name: "Facebook", icon: "📘", color: "bg-blue-600 hover:bg-blue-700" },
    { id: "twitter", name: "Twitter", icon: "🐦", color: "bg-sky-500 hover:bg-sky-600" },
    { id: "linkedin", name: "LinkedIn", icon: "💼", color: "bg-blue-700 hover:bg-blue-800" },
    { id: "whatsapp", name: "WhatsApp", icon: "💬", color: "bg-green-600 hover:bg-green-700" },
    { id: "email", name: "Email", icon: "📧", color: "bg-gray-600 hover:bg-gray-700" }
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white font-semibold flex items-center gap-2"
        disabled={isSharing}
      >
        {isSharing ? "Sharing..." : "📤 Share"}
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-lg z-10 min-w-[200px]">
          <div className="text-sm text-gray-300 mb-3">Share this event:</div>
          <div className="space-y-2">
            {shareOptions.map(option => (
              <button
                key={option.id}
                onClick={() => shareEvent(option.id)}
                className={`w-full px-3 py-2 ${option.color} rounded-lg text-white text-sm flex items-center gap-2`}
                disabled={isSharing}
              >
                <span>{option.icon}</span>
                {option.name}
              </button>
            ))}
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="mt-3 w-full px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-white text-sm"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
