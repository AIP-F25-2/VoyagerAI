"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  features: string[];
  limits: {
    saved_events: number;
    reviews: number;
  };
}

interface SubscriptionStatus {
  plan: string;
  status: string;
  limits: {
    saved_events: number;
    reviews: number;
  };
  usage: {
    saved_events: number;
    reviews: number;
  };
  expires_at?: string;
}

export default function SubscriptionStatus() {
  const [isClient, setIsClient] = useState(false);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpgrading, setIsUpgrading] = useState(false);
  
  // Get auth context only on client side
  let user = null;
  try {
    const authContext = useAuth();
    user = authContext?.user;
  } catch (error) {
    // Auth context not available (server-side rendering)
    user = null;
  }

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (user?.email) {
      loadPlans();
      loadSubscriptionStatus();
    }
  }, [user]);

  const loadPlans = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/subscription/plans");
      const data = await response.json();
      
      if (data.success) {
        setPlans(data.plans);
      }
    } catch (error) {
      console.error("Failed to load plans:", error);
    }
  };

  const loadSubscriptionStatus = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/subscription/status?email=${user?.email}`);
      const data = await response.json();
      
      if (data.success) {
        setSubscription(data.subscription);
      }
    } catch (error) {
      console.error("Failed to load subscription status:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const upgradeSubscription = async (planId: string) => {
    if (!user?.email) return;

    setIsUpgrading(true);
    
    try {
      const response = await fetch("http://localhost:5000/api/subscription/upgrade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user.email,
          plan: planId
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert(`Successfully upgraded to ${planId} plan!`);
        loadSubscriptionStatus(); // Reload status
      } else {
        alert(data.message || "Failed to upgrade subscription");
      }
    } catch (error) {
      console.error("Upgrade error:", error);
      alert("Failed to upgrade subscription");
    } finally {
      setIsUpgrading(false);
    }
  };

  const getPlanColor = (planName: string) => {
    switch (planName.toLowerCase()) {
      case 'free': return 'bg-gray-600';
      case 'premium': return 'bg-blue-600';
      case 'pro': return 'bg-purple-600';
      default: return 'bg-gray-600';
    }
  };

  const getUsageColor = (used: number, limit: number) => {
    const percentage = (used / limit) * 100;
    if (percentage >= 90) return 'text-red-400';
    if (percentage >= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  // Don't render on server side
  if (!isClient) {
    return <div className="p-4 text-center text-gray-400">Loading subscription status...</div>;
  }

  if (isLoading) {
    return <div className="p-4 text-center text-gray-400">Loading subscription status...</div>;
  }

  if (!user) {
    return (
      <div className="bg-gray-800/50 p-6 rounded-lg">
        <div className="text-center text-gray-400">
          Sign in to view your subscription status
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Subscription Status */}
      <div className="bg-gray-800/50 p-6 rounded-lg">
        <h2 className="text-xl font-semibold text-white mb-4">Your Subscription</h2>
        
        {subscription ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold text-white ${getPlanColor(subscription.plan)}`}>
                  {subscription.plan.toUpperCase()} PLAN
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  Status: {subscription.status}
                </div>
              </div>
              {subscription.expires_at && (
                <div className="text-sm text-gray-400">
                  Expires: {new Date(subscription.expires_at).toLocaleDateString()}
                </div>
              )}
            </div>

            {/* Usage Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-700/50 rounded-lg">
                <div className="text-sm text-gray-300">Saved Events</div>
                <div className={`text-lg font-semibold ${getUsageColor(subscription.usage.saved_events, subscription.limits.saved_events)}`}>
                  {subscription.usage.saved_events} / {subscription.limits.saved_events === -1 ? '∞' : subscription.limits.saved_events}
                </div>
              </div>
              <div className="p-3 bg-gray-700/50 rounded-lg">
                <div className="text-sm text-gray-300">Reviews</div>
                <div className={`text-lg font-semibold ${getUsageColor(subscription.usage.reviews, subscription.limits.reviews)}`}>
                  {subscription.usage.reviews} / {subscription.limits.reviews === -1 ? '∞' : subscription.limits.reviews}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-400">
            No subscription found
          </div>
        )}
      </div>

      {/* Available Plans */}
      <div className="bg-gray-800/50 p-6 rounded-lg">
        <h2 className="text-xl font-semibold text-white mb-4">Available Plans</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.map(plan => (
            <div
              key={plan.id}
              className={`p-4 rounded-lg border-2 ${
                subscription?.plan.toLowerCase() === plan.id
                  ? 'border-blue-500 bg-blue-900/20'
                  : 'border-gray-600 bg-gray-700/30'
              }`}
            >
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                <div className="text-2xl font-bold text-white mt-2">
                  {plan.price === 0 ? 'Free' : `$${plan.price}/${plan.currency === 'USD' ? 'mo' : plan.currency}`}
                </div>
              </div>

              <div className="space-y-2 mb-4">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm text-gray-300">
                    <span className="text-green-400">✓</span>
                    {feature}
                  </div>
                ))}
              </div>

              <div className="text-xs text-gray-400 mb-4">
                <div>Saved Events: {plan.limits.saved_events === -1 ? 'Unlimited' : plan.limits.saved_events}</div>
                <div>Reviews: {plan.limits.reviews === -1 ? 'Unlimited' : plan.limits.reviews}</div>
              </div>

              {subscription?.plan.toLowerCase() !== plan.id && (
                <button
                  onClick={() => upgradeSubscription(plan.id)}
                  disabled={isUpgrading}
                  className={`w-full py-2 px-4 rounded-lg font-semibold text-white transition-colors ${
                    plan.id === 'free'
                      ? 'bg-gray-600 hover:bg-gray-700'
                      : plan.id === 'premium'
                      ? 'bg-blue-600 hover:bg-blue-700'
                      : 'bg-purple-600 hover:bg-purple-700'
                  } disabled:opacity-50`}
                >
                  {isUpgrading ? 'Processing...' : plan.id === 'free' ? 'Downgrade' : 'Upgrade'}
                </button>
              )}

              {subscription?.plan.toLowerCase() === plan.id && (
                <div className="w-full py-2 px-4 rounded-lg bg-green-600 text-white text-center font-semibold">
                  Current Plan
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
