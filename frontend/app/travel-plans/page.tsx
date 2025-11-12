'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/apiClient'
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
  const [savedEvents, setSavedEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showSavedEvents, setShowSavedEvents] = useState(false)
  const [newItinerary, setNewItinerary] = useState({
    title: '',
    description: '',
    destination: '',
    start_date: '',
    end_date: '',
    budget: ''
  })
  const [selectedEvents, setSelectedEvents] = useState<any[]>([])
  const [showEventSelector, setShowEventSelector] = useState(false)

  useEffect(() => {
    // Add a small delay to ensure authentication context is loaded
    const timer = setTimeout(() => {
      if (isAuthenticated && user?.id) {
        console.log('User authenticated, fetching data for user:', user.id)
        fetchItineraries()
        fetchSavedEvents()
      } else {
        console.log('User not authenticated or no user ID')
        setLoading(false)
      }
    }, 100)

    return () => clearTimeout(timer)
  }, [isAuthenticated, user])

  const fetchItineraries = async () => {
    try {
      console.log('Fetching itineraries for user ID:', user?.id)
      const data = await apiClient.get(`/api/itineraries?user_id=${user?.id}`)
      console.log('Fetch response data:', data)
      
      if (data.success) {
        setTravelPlans(data.itineraries)
      } else {
        console.error('Failed to fetch itineraries:', data.error)
      }
    } catch (error) {
      console.error('Failed to fetch travel plans:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSavedEvents = async () => {
    try {
      const data = await apiClient.get(`/api/favorites?user_email=${user?.email}`)
      if (data.success) {
        setSavedEvents(data.favorites)
      }
    } catch (error) {
      console.error('Failed to fetch saved events:', error)
    }
  }

  const addEventToTravelPlan = async (travelPlanId: number, event: any) => {
    try {
      const data = await apiClient.post(`/api/itineraries/${travelPlanId}/items`, {
        item_type: 'event',
        title: event.title,
        description: event.venue || '',
        date: event.date || '',
        time: '',
        location: event.venue || '',
        price: event.price ? parseFloat(event.price.replace(/[^0-9.]/g, '')) : 0,
        url: event.url || '',
        image_url: '',
        status: 'planned',
        order_index: 0
      })
      if (data.success) {
        alert('Event added to travel plan successfully!')
        fetchItineraries() // Refresh the travel plans
      } else {
        alert('Failed to add event to travel plan')
      }
    } catch (error) {
      console.error('Failed to add event to travel plan:', error)
      alert('Failed to add event to travel plan')
    }
  }

  const toggleEventSelection = (event: any) => {
    setSelectedEvents(prev => {
      const isSelected = prev.some(e => e.title === event.title)
      if (isSelected) {
        return prev.filter(e => e.title !== event.title)
      } else {
        return [...prev, event]
      }
    })
  }

  const removeSelectedEvent = (eventToRemove: any) => {
    setSelectedEvents(prev => prev.filter(e => e.title !== eventToRemove.title))
  }

  const handleCreateItinerary = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Check if user is authenticated
    if (!user?.id) {
      alert('Please log in to create a travel plan')
      return
    }
    
    try {
      console.log('Creating itinerary with user ID:', user.id)
      console.log('Itinerary data:', {
        user_id: user.id,
        ...newItinerary,
        budget: newItinerary.budget ? parseFloat(newItinerary.budget) : null
      })
      
      const data = await apiClient.post('/api/itineraries', {
        user_id: user.id,
        ...newItinerary,
        budget: newItinerary.budget ? parseFloat(newItinerary.budget) : null
      })
      console.log('Response data:', data)
      
      if (data.success) {
        const newItineraryId = data.itinerary.id
        
        // Add selected events to the new itinerary
        if (selectedEvents.length > 0) {
          for (const event of selectedEvents) {
            await addEventToTravelPlan(newItineraryId, event)
          }
        }
        
        setTravelPlans([data.itinerary, ...travelPlans])
        setNewItinerary({
          title: '',
          description: '',
          destination: '',
          start_date: '',
          end_date: '',
          budget: ''
        })
        setSelectedEvents([])
        setShowCreateForm(false)
        fetchItineraries() // Refresh to show the new plan with events
        alert('Travel plan created successfully!')
      } else {
        console.error('Backend error:', data)
        alert(data.error || 'Failed to create travel plan')
      }
    } catch (error) {
      console.error('Failed to create travel plan:', error)
      alert('Failed to create travel plan: ' + error.message)
    }
  }

  const handleDeleteItinerary = async (id: number) => {
    if (!confirm('Are you sure you want to delete this travel plan?')) return

    try {
      const data = await apiClient.delete(`/api/itineraries/${id}`)
      
      if (data.success) {
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

  // Show loading state while authentication is being checked
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-xl">Loading your travel plans...</p>
        </div>
      </div>
    )
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
          <div className="flex gap-3">
            <button
              onClick={() => setShowSavedEvents(!showSavedEvents)}
              className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold"
            >
              📅 Saved Events ({savedEvents.length})
            </button>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold"
            >
              + Create New Travel Plan
            </button>
          </div>
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
              {/* Selected Events Display */}
              {selectedEvents.length > 0 && (
                <div className="bg-gray-700/50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3">Selected Events ({selectedEvents.length})</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {selectedEvents.map((event, index) => (
                      <div key={index} className="bg-gray-600/50 p-3 rounded-lg flex justify-between items-center">
                        <div>
                          <h4 className="font-medium">{event.title}</h4>
                          {event.venue && <p className="text-sm text-gray-300">📍 {event.venue}</p>}
                          {event.date && <p className="text-sm text-gray-300">📅 {event.date}</p>}
                        </div>
                        <button
                          type="button"
                          onClick={() => removeSelectedEvent(event)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          ✕ Remove
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Event Selection Section */}
              <div className="border-t border-gray-600 pt-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Add Events to Your Plan</h3>
                  <button
                    type="button"
                    onClick={() => setShowEventSelector(!showEventSelector)}
                    className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-sm"
                  >
                    {showEventSelector ? 'Hide Events' : 'Select Events'}
                  </button>
                </div>
                
                {showEventSelector && (
                  <div className="bg-gray-700/30 p-4 rounded-lg">
                    {savedEvents.length === 0 ? (
                      <p className="text-gray-400 text-center py-4">No saved events yet. Go to the main page and save some events!</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {savedEvents.map((event, index) => {
                          const isSelected = selectedEvents.some(e => e.title === event.title)
                          return (
                            <div 
                              key={index} 
                              className={`p-3 rounded-lg cursor-pointer transition-colors ${
                                isSelected 
                                  ? 'bg-blue-600/50 border-2 border-blue-400' 
                                  : 'bg-gray-600/50 hover:bg-gray-500/50'
                              }`}
                              onClick={() => toggleEventSelection(event)}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-medium text-sm">{event.title}</h4>
                                {isSelected && <span className="text-blue-400">✓</span>}
                              </div>
                              {event.venue && <p className="text-xs text-gray-300 mb-1">📍 {event.venue}</p>}
                              {event.date && <p className="text-xs text-gray-300 mb-1">📅 {event.date}</p>}
                              {event.price && <p className="text-xs text-green-400">💰 {event.price}</p>}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg"
                >
                  Create Itinerary {selectedEvents.length > 0 && `(${selectedEvents.length} events)`}
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

        {/* Saved Events Section */}
        {showSavedEvents && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <h2 className="text-xl font-bold mb-4">Your Saved Events</h2>
            {savedEvents.length === 0 ? (
              <p className="text-gray-400 text-center py-4">No saved events yet. Go to the main page and save some events!</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedEvents.map((event, index) => (
                  <div key={index} className="bg-gray-700/50 p-4 rounded-lg">
                    <h3 className="font-semibold mb-2">{event.title}</h3>
                    {event.venue && <p className="text-sm text-gray-300 mb-2">📍 {event.venue}</p>}
                    {event.date && <p className="text-sm text-gray-300 mb-2">📅 {event.date}</p>}
                    {event.price && <p className="text-sm text-green-400 mb-2">💰 {event.price}</p>}
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => {
                          // Add event to a travel plan
                          const travelPlanId = prompt('Enter travel plan ID to add this event to:')
                          if (travelPlanId) {
                            addEventToTravelPlan(parseInt(travelPlanId), event)
                          }
                        }}
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                      >
                        Add to Plan
                      </button>
                      <a
                        href={event.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm"
                      >
                        View Event
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
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
