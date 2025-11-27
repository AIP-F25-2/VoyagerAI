"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface Review {
  id: number;
  user_email: string;
  rating: number;
  review_text: string;
  created_at: string;
  updated_at: string;
  event_date?: string;
}

interface EnhancedEventReviewsProps {
  eventTitle: string;
  eventUrl?: string;
  eventDate?: string;
  compact?: boolean;
}

export default function EnhancedEventReviews({
  eventTitle,
  eventUrl,
  eventDate,
  compact = false,
}: EnhancedEventReviewsProps) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [averageRating, setAverageRating] = useState(0);
  const [totalReviews, setTotalReviews] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, text: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ratingDistribution, setRatingDistribution] = useState<number[]>([]);

  useEffect(() => {
    loadReviews();
  }, [eventTitle, eventDate]);

  const loadReviews = async () => {
    try {
      const params = new URLSearchParams({
        event_title: eventTitle,
        ...(eventUrl && { event_url: eventUrl }),
        limit: "50",
      });

      const response = await fetch(`/api/events/reviews?${params}`);
      const data = await response.json();

      if (data.success) {
        setReviews(data.reviews || []);
        setAverageRating(data.average_rating || 0);
        setTotalReviews(data.total_reviews || 0);
        calculateRatingDistribution(data.reviews || []);
      }
    } catch (error) {
      console.error("Failed to load reviews:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateRatingDistribution = (reviewList: Review[]) => {
    const distribution = [0, 0, 0, 0, 0]; // 5, 4, 3, 2, 1 stars
    reviewList.forEach((review) => {
      if (review.rating >= 1 && review.rating <= 5) {
        distribution[5 - review.rating]++;
      }
    });
    setRatingDistribution(distribution);
  };

  const submitReview = async () => {
    if (!user?.email) {
      alert("Please log in to write a review");
      return;
    }

    if (!newReview.text.trim()) {
      alert("Please write a review");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/events/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user.email,
          event_title: eventTitle,
          event_url: eventUrl,
          event_date: eventDate,
          rating: newReview.rating,
          review_text: newReview.text,
        }),
      });

      const data = await response.json();

      if (data.success) {
        alert("Review submitted successfully!");
        setNewReview({ rating: 5, text: "" });
        setShowReviewForm(false);
        loadReviews();
      } else {
        alert(data.error || "Failed to submit review");
      }
    } catch (error) {
      console.error("Review submission error:", error);
      alert("Failed to submit review");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = (
    rating: number,
    interactive = false,
    onChange?: (rating: number) => void,
    size: "sm" | "md" | "lg" = "md"
  ) => {
    const sizeClasses = {
      sm: "text-sm",
      md: "text-lg",
      lg: "text-2xl",
    };

    return (
      <div className={`flex gap-0.5 ${sizeClasses[size]}`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => interactive && onChange?.(star)}
            onMouseEnter={() => interactive && onChange?.(star)}
            className={`transition-all ${
              star <= rating
                ? "text-yellow-400 fill-yellow-400"
                : "text-gray-400 fill-gray-400"
            } ${interactive ? "hover:text-yellow-300 hover:fill-yellow-300 cursor-pointer" : ""}`}
            disabled={!interactive}
          >
            <svg
              className="w-5 h-5"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
            </svg>
          </button>
        ))}
      </div>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="p-4 text-center text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2">Loading reviews...</p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        {averageRating > 0 && (
          <>
            <div className="flex items-center gap-1">
              {renderStars(Math.round(averageRating), false, undefined, "sm")}
              <span className="text-white font-semibold">{averageRating.toFixed(1)}</span>
            </div>
            <span className="text-gray-400 text-sm">({totalReviews})</span>
          </>
        )}
        {user && (
          <button
            onClick={() => setShowReviewForm(true)}
            className="text-blue-400 hover:text-blue-300 text-sm underline"
          >
            Write Review
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white mb-2">Reviews & Ratings</h3>
          {averageRating > 0 && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-4xl font-bold text-white">{averageRating.toFixed(1)}</span>
                <div className="flex flex-col">
                  {renderStars(Math.round(averageRating), false, undefined, "md")}
                  <span className="text-gray-400 text-sm mt-1">
                    {totalReviews} {totalReviews === 1 ? "review" : "reviews"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
        {user && (
          <button
            onClick={() => setShowReviewForm(!showReviewForm)}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-semibold transition-all"
          >
            {showReviewForm ? "Cancel" : "✍️ Write Review"}
          </button>
        )}
      </div>

      {/* Rating Distribution */}
      {ratingDistribution.some((count) => count > 0) && (
        <div className="mb-6 p-4 bg-gray-700/30 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">Rating Distribution</h4>
          <div className="space-y-2">
            {[5, 4, 3, 2, 1].map((stars, index) => {
              const count = ratingDistribution[index];
              const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
              return (
                <div key={stars} className="flex items-center gap-3">
                  <span className="text-gray-400 text-sm w-12">{stars} star</span>
                  <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-yellow-400 transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-gray-400 text-sm w-12 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Review Form */}
      {showReviewForm && (
        <div className="mb-6 p-5 bg-gradient-to-br from-blue-900/30 to-purple-900/30 rounded-lg border border-blue-500/30">
          <h4 className="text-lg font-semibold text-white mb-4">Share Your Experience</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Your Rating
              </label>
              <div className="flex items-center gap-3">
                {renderStars(newReview.rating, true, (rating) =>
                  setNewReview({ ...newReview, rating })
                )}
                <span className="text-white font-semibold">{newReview.rating} out of 5</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Your Review
              </label>
              <textarea
                value={newReview.text}
                onChange={(e) => setNewReview({ ...newReview, text: e.target.value })}
                placeholder="Tell others about your experience at this event..."
                className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white placeholder-gray-400"
                rows={4}
              />
              <p className="text-xs text-gray-400 mt-1">
                {newReview.text.length}/500 characters
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={submitReview}
                disabled={isSubmitting || !newReview.text.trim()}
                className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-semibold transition-all"
              >
                {isSubmitting ? "Submitting..." : "Submit Review"}
              </button>
              <button
                onClick={() => {
                  setShowReviewForm(false);
                  setNewReview({ rating: 5, text: "" });
                }}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg text-white"
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
          <div className="text-center py-12">
            <div className="text-6xl mb-4">⭐</div>
            <h4 className="text-lg font-semibold text-gray-300 mb-2">No reviews yet</h4>
            <p className="text-gray-400 mb-4">Be the first to share your experience!</p>
            {user && (
              <button
                onClick={() => setShowReviewForm(true)}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-semibold"
              >
                Write the First Review
              </button>
            )}
          </div>
        ) : (
          reviews.map((review) => (
            <div
              key={review.id}
              className="p-4 bg-gray-700/30 rounded-lg border border-gray-600/50 hover:border-gray-500/50 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-sm">
                      {review.user_email.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="text-white font-medium">
                      {review.user_email.split("@")[0]}
                      {review.user_email === user?.email && (
                        <span className="ml-2 text-xs text-blue-400">(You)</span>
                      )}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {renderStars(review.rating, false, undefined, "sm")}
                      <span className="text-gray-400 text-xs">
                        {formatDate(review.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              {review.review_text && (
                <p className="text-gray-200 text-sm leading-relaxed mt-3 pl-13">
                  {review.review_text}
                </p>
              )}
            </div>
          ))
        )}
      </div>

      {/* Load More Button */}
      {reviews.length >= 10 && (
        <div className="mt-6 text-center">
          <button className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white text-sm">
            Load More Reviews
          </button>
        </div>
      )}
    </div>
  );
}

