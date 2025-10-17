'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useParams } from 'next/navigation'
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

export default function ItineraryDetailPage() {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useParams()
  const itineraryId = params.id as string

  const [itinerary, setItinerary] = useState<Itinerary | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddItemForm, setShowAddItemForm] = useState(false)
  const [newItem, setNewItem] = useState({
    item_type: 'activity',
    title: '',
    description: '',
    date: '',
    time: '',
    location: '',
    price: '',
    url: '',
    image_url: ''
  })

  useEffect(() => {
    if (isAuthenticated && user?.id && itineraryId) {
      fetchItinerary()
    }
  }, [isAuthenticated, user, itineraryId])

  const fetchItinerary = async () => {
    try {
      const response = await fetch(`/api/travel-plans/${itineraryId}`)
      const data = await response.json()
      if (data.success) {
        setItinerary(data.itinerary)
      } else {
        alert('Itinerary not found')
        router.push('/travel-plans')
      }
    } catch (error) {
      console.error('Failed to fetch travel plan:', error)
      alert('Failed to load travel plan')
    } finally {
      setLoading(false)
    }
  }

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch(`/api/travel-plans/${itineraryId}/items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...newItem,
          price: newItem.price ? parseFloat(newItem.price) : null,
          order_index: itinerary?.items?.length || 0
        }),
      })

      const data = await response.json()
      if (data.success) {
        setItinerary(prev => prev ? {
          ...prev,
          items: [...(prev.items || []), data.item]
        } : null)
        setNewItem({
          item_type: 'activity',
          title: '',
          description: '',
          date: '',
          time: '',
          location: '',
          price: '',
          url: '',
          image_url: ''
        })
        setShowAddItemForm(false)
      } else {
        alert(data.error || 'Failed to add item')
      }
    } catch (error) {
      console.error('Failed to add item:', error)
      alert('Failed to add item')
    }
  }

  const handleDeleteItem = async (itemId: number) => {
    if (!confirm('Are you sure you want to delete this item?')) return

    try {
      const response = await fetch(`/api/travel-plans/${itineraryId}/items/${itemId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setItinerary(prev => prev ? {
          ...prev,
          items: prev.items?.filter(item => item.id !== itemId) || []
        } : null)
      } else {
        alert('Failed to delete item')
      }
    } catch (error) {
      console.error('Failed to delete item:', error)
      alert('Failed to delete item')
    }
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

  const getItemTypeColor = (type: string) => {
    switch (type) {
      case 'event': return 'bg-purple-500'
      case 'hotel': return 'bg-blue-500'
      case 'flight': return 'bg-green-500'
      case 'activity': return 'bg-orange-500'
      case 'note': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'No date set'
    return new Date(dateString).toLocaleDateString()
  }

  const formatTime = (timeString: string) => {
    if (!timeString) return ''
    return new Date(`2000-01-01T${timeString}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const sortedItems = itinerary?.items?.sort((a, b) => {
    // Sort by date first, then by time, then by order_index
    if (a.date && b.date) {
      const dateCompare = new Date(a.date).getTime() - new Date(b.date).getTime()
      if (dateCompare !== 0) return dateCompare
    }
    if (a.time && b.time) {
      return a.time.localeCompare(b.time)
    }
    return a.order_index - b.order_index
  }) || []

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Please sign in to view this travel plan</h1>
          <Link href="/login" className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg">
            Sign In
          </Link>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading travel plan...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!itinerary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Travel plan not found</h1>
          <Link href="/travel-plans" className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg">
            Back to Travel Plans
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <Link href="/travel-plans" className="text-blue-400 hover:text-blue-300 mb-4 inline-block">
              ← Back to Travel Plans
            </Link>
            <h1 className="text-3xl font-bold mb-2">{itinerary.title}</h1>
            {itinerary.destination && (
              <p className="text-gray-300 text-lg">📍 {itinerary.destination}</p>
            )}
          </div>
          <div className="text-right">
            <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium text-white ${
              itinerary.status === 'draft' ? 'bg-gray-500' :
              itinerary.status === 'active' ? 'bg-green-500' :
              itinerary.status === 'completed' ? 'bg-blue-500' :
              'bg-red-500'
            }`}>
              {itinerary.status.charAt(0).toUpperCase() + itinerary.status.slice(1)}
            </div>
          </div>
        </div>

        {/* Itinerary Info */}
        <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-gray-300 mb-2">Duration</h3>
              <p className="text-lg">
                {formatDate(itinerary.start_date)} - {formatDate(itinerary.end_date)}
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-300 mb-2">Budget</h3>
              <p className="text-lg">
                {itinerary.budget ? `$${itinerary.budget.toLocaleString()}` : 'Not set'}
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-300 mb-2">Items</h3>
              <p className="text-lg">{itinerary.items?.length || 0} planned</p>
            </div>
          </div>
          {itinerary.description && (
            <div className="mt-6">
              <h3 className="font-semibold text-gray-300 mb-2">Description</h3>
              <p className="text-gray-300">{itinerary.description}</p>
            </div>
          )}
        </div>

        {/* Add Item Button */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Itinerary Items</h2>
          <button
            onClick={() => setShowAddItemForm(true)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
          >
            + Add Item
          </button>
        </div>

        {/* Add Item Form */}
        {showAddItemForm && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <h3 className="text-xl font-bold mb-4">Add New Item</h3>
            <form onSubmit={handleAddItem} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Type *</label>
                  <select
                    value={newItem.item_type}
                    onChange={(e) => setNewItem({...newItem, item_type: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                    required
                  >
                    <option value="activity">Activity</option>
                    <option value="event">Event</option>
                    <option value="hotel">Hotel</option>
                    <option value="flight">Flight</option>
                    <option value="note">Note</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Title *</label>
                  <input
                    type="text"
                    value={newItem.title}
                    onChange={(e) => setNewItem({...newItem, title: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Date</label>
                  <input
                    type="date"
                    value={newItem.date}
                    onChange={(e) => setNewItem({...newItem, date: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Time</label>
                  <input
                    type="time"
                    value={newItem.time}
                    onChange={(e) => setNewItem({...newItem, time: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Location</label>
                  <input
                    type="text"
                    value={newItem.location}
                    onChange={(e) => setNewItem({...newItem, location: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newItem.price}
                    onChange={(e) => setNewItem({...newItem, price: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={newItem.description}
                  onChange={(e) => setNewItem({...newItem, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex gap-4">
                <button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg"
                >
                  Add Item
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddItemForm(false)}
                  className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Items List */}
        {sortedItems.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold mb-2">No items yet</h3>
            <p className="text-gray-400 mb-6">Add items to start building your travel plan!</p>
            <button
              onClick={() => setShowAddItemForm(true)}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg"
            >
              Add Your First Item
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedItems.map((item, index) => (
              <div key={item.id} className="bg-gray-800/50 p-6 rounded-lg">
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white text-xl ${getItemTypeColor(item.item_type)}`}>
                      {getItemTypeIcon(item.item_type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold">{item.title}</h3>
                        <span className="text-sm text-gray-400 capitalize">{item.item_type}</span>
                      </div>
                      {item.description && (
                        <p className="text-gray-300 mb-3">{item.description}</p>
                      )}
                      <div className="flex flex-wrap gap-4 text-sm text-gray-400">
                        {item.date && (
                          <span>📅 {formatDate(item.date)}</span>
                        )}
                        {item.time && (
                          <span>🕐 {formatTime(item.time)}</span>
                        )}
                        {item.location && (
                          <span>📍 {item.location}</span>
                        )}
                        {item.price && (
                          <span>💰 ${item.price.toLocaleString()}</span>
                        )}
                      </div>
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block"
                        >
                          View Details →
                        </a>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteItem(item.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
