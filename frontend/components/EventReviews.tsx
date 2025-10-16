"use client";

import { useState, useEffect } from "react";

interface Review {
  id: number;
  user_email: string;
  rating: number;
  review_text: string;
  created_at: string;
  updated_at: string;
}

interface EventReviewsProps {
  eventTitle: string;
  eventDate?: string;
  userEmail?: string;
}

export default function EventReviews({ eventTitle, eventDate, userEmail }: EventReviewsProps) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [averageRating, setAverageRating] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, text: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadReviews();
  }, [eventTitle, eventDate]);

  const loadReviews = async () => {
    try {
      const params = new URLSearchParams({
        event_title: eventTitle,
        ...(eventDate && { event_date: eventDate })
      });

      const response = await fetch(`http://localhost:5000/api/events/reviews?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setReviews(data.reviews || []);
        setAverageRating(data.average_rating || 0);
      }
    } catch (error) {
      console.error("Failed to load reviews:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const submitReview = async () => {
    if (!userEmail) {
      alert("Please log in to write a review");
      return;
    }

    if (!newReview.text.trim()) {
      alert("Please write a review");
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await fetch("http://localhost:5000/api/events/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: userEmail,
          event_title: eventTitle,
          event_date: eventDate,
          rating: newReview.rating,
          review_text: newReview.text
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert("Review submitted successfully!");
        setNewReview({ rating: 5, text: "" });
        setShowReviewForm(false);
        loadReviews(); // Reload reviews
      } else {
        alert(data.message || "Failed to submit review");
      }
    } catch (error) {
      console.error("Review submission error:", error);
      alert("Failed to submit review");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = (rating: number, interactive = false, onChange?: (rating: number) => void) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            onClick={() => interactive && onChange?.(star)}
            className={`text-lg ${star <= rating ? 'text-yellow-400' : 'text-gray-400'} ${
              interactive ? 'hover:text-yellow-300 cursor-pointer' : ''
            }`}
            disabled={!interactive}
          >
            ★
          </button>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return <div className="p-4 text-center text-gray-400">Loading reviews...</div>;
  }

  return (
    <div className="bg-gray-800/50 p-6 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-white">Reviews & Ratings</h3>
        {userEmail && (
          <button
            onClick={() => setShowReviewForm(!showReviewForm)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm"
          >
            {showReviewForm ? "Cancel" : "Write Review"}
          </button>
        )}
      </div>

      {/* Average Rating */}
      {averageRating > 0 && (
        <div className="mb-4 p-4 bg-gray-700/50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="text-2xl font-bold text-white">{averageRating.toFixed(1)}</div>
            {renderStars(Math.round(averageRating))}
            <div className="text-gray-300">
              ({reviews.length} review{reviews.length !== 1 ? 's' : ''})
            </div>
          </div>
        </div>
      )}

      {/* Review Form */}
      {showReviewForm && (
        <div className="mb-6 p-4 bg-gray-700/50 rounded-lg">
          <h4 className="text-lg font-semibold text-white mb-3">Write a Review</h4>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Rating</label>
              {renderStars(newReview.rating, true, (rating) => 
                setNewReview({ ...newReview, rating })
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Review</label>
              <textarea
                value={newReview.text}
                onChange={(e) => setNewReview({ ...newReview, text: e.target.value })}
                placeholder="Share your experience..."
                className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                rows={3}
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={submitReview}
                disabled={isSubmitting}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg text-white"
              >
                {isSubmitting ? "Submitting..." : "Submit Review"}
              </button>
              <button
                onClick={() => setShowReviewForm(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reviews List */}
      <div className="space-y-4">
        {reviews.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No reviews yet. Be the first to review this event!
          </div>
        ) : (
          reviews.map(review => (
            <div key={review.id} className="p-4 bg-gray-700/30 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="text-sm text-gray-300">
                    {review.user_email.split('@')[0]}***
                  </div>
                  {renderStars(review.rating)}
                </div>
                <div className="text-xs text-gray-400">
                  {new Date(review.created_at).toLocaleDateString()}
                </div>
              </div>
              {review.review_text && (
                <p className="text-gray-200 text-sm">{review.review_text}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
