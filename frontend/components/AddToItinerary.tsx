'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface Itinerary {
  id: number
  title: string
  destination: string
  start_date: string
  end_date: string
}

interface AddToItineraryProps {
  itemType: 'event' | 'hotel' | 'flight'
  itemData: {
    title: string
    description?: string
    date?: string
    time?: string
    location?: string
    price?: number
    url?: string
    image_url?: string
  }
  onAdded?: () => void
}

export default function AddToItinerary({ itemType, itemData, onAdded }: AddToItineraryProps) {
  const { user, isAuthenticated } = useAuth()
  const [travelPlans, setTravelPlans] = useState<Itinerary[]>([])
  const [showModal, setShowModal] = useState(false)
  const [selectedItinerary, setSelectedItinerary] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated && user?.id && showModal) {
      fetchItineraries()
    }
  }, [isAuthenticated, user, showModal])

  const fetchItineraries = async () => {
    try {
      const response = await fetch(`/api/travel-plans?user_id=${user?.id}`)
      const data = await response.json()
      if (data.success) {
        setTravelPlans(data.travel_plans)
      }
    } catch (error) {
      console.error('Failed to fetch travel plans:', error)
    }
  }

  const handleAddToItinerary = async () => {
    if (!selectedItinerary) return

    setLoading(true)
    try {
      const response = await fetch(`/api/travel-plans/${selectedItinerary}/items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_type: itemType,
          title: itemData.title,
          description: itemData.description,
          date: itemData.date,
          time: itemData.time,
          location: itemData.location,
          price: itemData.price,
          url: itemData.url,
          image_url: itemData.image_url,
          order_index: 0
        }),
      })

      const data = await response.json()
      if (data.success) {
        setShowModal(false)
        setSelectedItinerary(null)
        if (onAdded) onAdded()
        alert('Item added to travel plan successfully!')
      } else {
        alert(data.error || 'Failed to add item to travel plan')
      }
    } catch (error) {
      console.error('Failed to add item to travel plan:', error)
      alert('Failed to add item to travel plan')
    } finally {
      setLoading(false)
    }
  }

  const getItemTypeIcon = (type: string) => {
    switch (type) {
      case 'event': return '🎵'
      case 'hotel': return '🏨'
      case 'flight': return '✈️'
      default: return '📍'
    }
  }

  const getItemTypeColor = (type: string) => {
    switch (type) {
      case 'event': return 'bg-purple-500'
      case 'hotel': return 'bg-blue-500'
      case 'flight': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-white transition-colors ${getItemTypeColor(itemType)} hover:opacity-90`}
      >
        {getItemTypeIcon(itemType)} Add to Itinerary
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Add to Itinerary</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-lg ${getItemTypeColor(itemType)}`}>
                    {getItemTypeIcon(itemType)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{itemData.title}</h3>
                    <p className="text-sm text-gray-500 capitalize">{itemType}</p>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Itinerary
                </label>
                {travelPlans.length === 0 ? (
                  <div className="text-center py-4">
                    <p className="text-gray-500 mb-4">No travel plans found</p>
                    <a
                      href="/travel-plans"
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      Create your first travel plan →
                    </a>
                  </div>
                ) : (
                  <select
                    value={selectedItinerary || ''}
                    onChange={(e) => setSelectedItinerary(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  >
                    <option value="">Choose a travel plan...</option>
                    {travelPlans.map((itinerary) => (
                      <option key={itinerary.id} value={itinerary.id}>
                        {itinerary.title} {itinerary.destination && `- ${itinerary.destination}`}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleAddToItinerary}
                  disabled={!selectedItinerary || loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  {loading ? 'Adding...' : 'Add to Itinerary'}
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
