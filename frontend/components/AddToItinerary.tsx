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
  const [creatingPlan, setCreatingPlan] = useState(false)
  const [newPlan, setNewPlan] = useState({
    title: '',
    destination: '',
  })

  useEffect(() => {
    if (isAuthenticated && user?.id && showModal) {
      fetchItineraries()
    }
  }, [isAuthenticated, user, showModal])

  const fetchItineraries = async () => {
    try {
      // Hit backend directly via rewrite using canonical backend route name
      const response = await fetch(`/api/itineraries?user_id=${user?.id}`)
      const data = await response.json()
      if (data.success) {
        // Backend returns key `itineraries`; normalize here for the modal
        setTravelPlans(data.itineraries || data.travel_plans || [])
      }
    } catch (error) {
      console.error('Failed to fetch travel plans:', error)
    }
  }

  const handleCreateItinerary = async () => {
    if (!user?.id || !newPlan.title.trim()) return
    setCreatingPlan(true)
    try {
      const res = await fetch('/api/travel-plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number.parseInt(user.id),
          title: newPlan.title.trim(),
          destination: newPlan.destination.trim() || undefined,
          status: 'draft',
        }),
      })
      const data = await res.json()
      if (res.ok && data.success && data.itinerary) {
        // Refresh list and preselect the new plan
        await fetchItineraries()
        setSelectedItinerary(data.itinerary.id)
        setNewPlan({ title: '', destination: '' })
        alert('Travel plan created')
      } else {
        alert(data.error || 'Failed to create travel plan')
      }
    } catch (e) {
      alert('Failed to create travel plan')
    } finally {
      setCreatingPlan(false)
    }
  }

  const handleAddToItinerary = async () => {
    if (!selectedItinerary) return

    setLoading(true)
    try {
      // Use backend route name so Next.js rewrite proxies correctly
      const response = await fetch(`/api/itineraries/${selectedItinerary}/items`, {
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
          status: 'planned',
          order_index: 0
        }),
      })

      const data = await response.json()
      if (response.ok && data.success) {
        setShowModal(false)
        setSelectedItinerary(null)
        if (onAdded) onAdded()
        alert('Item added to travel plan successfully!')
      } else {
        alert(data.error || `Failed to add item to travel plan`)
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
                {!travelPlans || travelPlans.length === 0 ? (
                  <div className="space-y-3">
                    <div className="text-gray-600 text-sm">No travel plans found. Create one:</div>
                    <input
                      type="text"
                      placeholder="Trip title (e.g., Toronto Weekend)"
                      value={newPlan.title}
                      onChange={(e)=>setNewPlan({...newPlan, title: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                    <input
                      type="text"
                      placeholder="Destination (optional)"
                      value={newPlan.destination}
                      onChange={(e)=>setNewPlan({...newPlan, destination: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={handleCreateItinerary}
                      disabled={!newPlan.title.trim() || creatingPlan}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg"
                    >
                      {creatingPlan ? 'Creating...' : 'Create Travel Plan'}
                    </button>
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
