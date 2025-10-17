'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface Itinerary {
  id: number
  user_id: number
  title: string
  description: string
  destination: string
  start_date: string
  end_date: string
  budget: number
  status: string
  created_at: string
  updated_at: string
  items: ItineraryItem[]
}

interface ItineraryItem {
  id: number
  itinerary_id: number
  item_type: string
  title: string
  description: string
  date: string
  time: string
  location: string
  price: number
  url: string
  image_url: string
  status: string
  order_index: number
}

export default function ItinerariesPage() {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const [travelPlans, setTravelPlans] = useState<Itinerary[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newItinerary, setNewItinerary] = useState({
    title: '',
    description: '',
    destination: '',
    start_date: '',
    end_date: '',
    budget: ''
  })

  useEffect(() => {
    if (isAuthenticated && user?.id) {
      fetchItineraries()
    }
  }, [isAuthenticated, user])

  const fetchItineraries = async () => {
    try {
      const response = await fetch(`/api/travel-plans?user_id=${user?.id}`)
      const data = await response.json()
      if (data.success) {
        setTravelPlans(data.travel_plans)
      }
    } catch (error) {
      console.error('Failed to fetch travel plans:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateItinerary = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/travel-plans', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          ...newItinerary,
          budget: newItinerary.budget ? parseFloat(newItinerary.budget) : null
        }),
      })

      const data = await response.json()
      if (data.success) {
        setTravelPlans([data.travel_plan, ...travelPlans])
        setNewItinerary({
          title: '',
          description: '',
          destination: '',
          start_date: '',
          end_date: '',
          budget: ''
        })
        setShowCreateForm(false)
      } else {
        alert(data.error || 'Failed to create travel plan')
      }
    } catch (error) {
      console.error('Failed to create travel plan:', error)
      alert('Failed to create travel plan')
    }
  }

  const handleDeleteItinerary = async (id: number) => {
    if (!confirm('Are you sure you want to delete this travel plan?')) return

    try {
      const response = await fetch(`/api/travel-plans/${id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setTravelPlans(travelPlans.filter(travelPlan => travelPlan.id !== id))
      } else {
        alert('Failed to delete travel plan')
      }
    } catch (error) {
      console.error('Failed to delete travel plan:', error)
      alert('Failed to delete travel plan')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-500'
      case 'active': return 'bg-green-500'
      case 'completed': return 'bg-blue-500'
      case 'cancelled': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'No date set'
    return new Date(dateString).toLocaleDateString()
  }

  const getItemTypeIcon = (type: string) => {
    switch (type) {
      case 'event': return '🎵'
      case 'hotel': return '🏨'
      case 'flight': return '✈️'
      case 'activity': return '🎯'
      case 'note': return '📝'
      default: return '📍'
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Please sign in to view your travel plans</h1>
          <Link href="/login" className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg">
            Sign In
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">My Travel Plans</h1>
            <p className="text-gray-300 mt-2">Plan and organize your trips</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold"
          >
            + Create New Travel Plan
          </button>
        </div>

        {/* Create Itinerary Form */}
        {showCreateForm && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <h2 className="text-xl font-bold mb-4">Create New Travel Plan</h2>
            <form onSubmit={handleCreateItinerary} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Title *</label>
                  <input
                    type="text"
                    value={newItinerary.title}
                    onChange={(e) => setNewItinerary({...newItinerary, title: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Destination</label>
                  <input
                    type="text"
                    value={newItinerary.destination}
                    onChange={(e) => setNewItinerary({...newItinerary, destination: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Start Date</label>
                  <input
                    type="date"
                    value={newItinerary.start_date}
                    onChange={(e) => setNewItinerary({...newItinerary, start_date: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Date</label>
                  <input
                    type="date"
                    value={newItinerary.end_date}
                    onChange={(e) => setNewItinerary({...newItinerary, end_date: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Budget ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newItinerary.budget}
                    onChange={(e) => setNewItinerary({...newItinerary, budget: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={newItinerary.description}
                  onChange={(e) => setNewItinerary({...newItinerary, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex gap-4">
                <button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg"
                >
                  Create Itinerary
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Itineraries List */}
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading travel plans...</p>
          </div>
        ) : travelPlans.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🗺️</div>
            <h3 className="text-xl font-semibold mb-2">No travel plans yet</h3>
            <p className="text-gray-400 mb-6">Create your first travel plan to start planning your trips!</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg"
            >
              Create Your First Travel Plan
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {travelPlans.map((travelPlan) => (
              <div key={travelPlan.id} className="bg-gray-800/50 p-6 rounded-lg hover:bg-gray-800/70 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold mb-2">{travelPlan.title}</h3>
                    <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(travelPlan.status)}`}>
                      {travelPlan.status.charAt(0).toUpperCase() + travelPlan.status.slice(1)}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      href={`/travel-plans/${travelPlan.id}`}
                      className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => handleDeleteItinerary(travelPlan.id)}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {travelPlan.destination && (
                  <p className="text-gray-300 mb-2">📍 {travelPlan.destination}</p>
                )}

                <div className="text-sm text-gray-400 mb-4">
                  <p>📅 {formatDate(travelPlan.start_date)} - {formatDate(travelPlan.end_date)}</p>
                  {travelPlan.budget && (
                    <p>💰 ${travelPlan.budget.toLocaleString()}</p>
                  )}
                </div>

                {travelPlan.description && (
                  <p className="text-gray-300 text-sm mb-4 line-clamp-2">{travelPlan.description}</p>
                )}

                <div className="border-t border-gray-700 pt-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">
                      {travelPlan.items?.length || 0} items
                    </span>
                    <span className="text-gray-500">
                      {new Date(travelPlan.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                  
                  {travelPlan.items && travelPlan.items.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {travelPlan.items.slice(0, 3).map((item, index) => (
                        <span key={index} className="text-xs bg-gray-700 px-2 py-1 rounded">
                          {getItemTypeIcon(item.item_type)} {item.title}
                        </span>
                      ))}
                      {travelPlan.items.length > 3 && (
                        <span className="text-xs text-gray-400">
                          +{travelPlan.items.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
