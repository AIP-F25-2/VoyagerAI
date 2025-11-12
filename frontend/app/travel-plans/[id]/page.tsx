'use client'

import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useParams } from 'next/navigation'
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

export default function ItineraryDetailPage() {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useParams()
  const itineraryId = params.id as string

  const [itinerary, setItinerary] = useState<Itinerary | null>(null)
  const [savedEvents, setSavedEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddItemForm, setShowAddItemForm] = useState(false)
  const [showSavedEvents, setShowSavedEvents] = useState(false)
  const [showHotelSearch, setShowHotelSearch] = useState(false)
  const [hotelSearchResults, setHotelSearchResults] = useState<any[]>([])
  const [hotelSearchCity, setHotelSearchCity] = useState('Toronto')
  const [hotelSearchLoading, setHotelSearchLoading] = useState(false)
  const [showBudgetEdit, setShowBudgetEdit] = useState(false)
  const [newBudget, setNewBudget] = useState('')
  const [showExportModal, setShowExportModal] = useState(false)
  const [generatingAI, setGeneratingAI] = useState(false)
  const [showAIGenerateModal, setShowAIGenerateModal] = useState(false)
  const [aiHints, setAiHints] = useState('')
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
    // Add a small delay to ensure authentication context is loaded
    const timer = setTimeout(() => {
      if (isAuthenticated && user?.id && itineraryId) {
        console.log('User authenticated, fetching itinerary for user:', user.id)
        fetchItinerary()
        fetchSavedEvents()
      } else {
        console.log('User not authenticated or no user ID or itinerary ID')
        setLoading(false)
      }
    }, 100)

    return () => clearTimeout(timer)
  }, [isAuthenticated, user, itineraryId])

  const fetchItinerary = async () => {
    try {
      console.log('Fetching itinerary with ID:', itineraryId)
      const data = await apiClient.get(`/api/itineraries/${itineraryId}`)
      console.log('Response data:', data)
      
      if (data.success) {
        setItinerary(data.itinerary)
      } else {
        console.error('Itinerary not found:', data.error)
        alert('Itinerary not found')
        router.push('/travel-plans')
      }
    } catch (error) {
      console.error('Failed to fetch travel plan:', error)
      alert('Failed to load travel plan: ' + error.message)
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

  const searchHotels = async () => {
    if (!hotelSearchCity.trim()) return
    
    setHotelSearchLoading(true)
    try {
      const response = await fetch(`/api/hotels/search?city=${encodeURIComponent(hotelSearchCity)}&limit=10`)
      const data = await response.json()
      if (data.success) {
        setHotelSearchResults(data.hotels || [])
      } else {
        setHotelSearchResults([])
      }
    } catch (error) {
      console.error('Failed to search hotels:', error)
      setHotelSearchResults([])
    } finally {
      setHotelSearchLoading(false)
    }
  }

  const addHotelToItinerary = async (hotel: any) => {
    try {
      const data = await apiClient.post(`/api/itineraries/${itineraryId}/items`, {
        item_type: 'hotel',
        title: hotel.name,
        description: hotel.address || hotel.location || '',
        date: itinerary?.start_date || '',
        time: '15:00', // Default check-in time
        location: hotel.address || hotel.location || '',
        price: hotel.price_per_night ? Number.parseFloat(hotel.price_per_night.replace(/[^0-9.]/g, '')) : null,
        url: hotel.url || '',
        image_url: '',
        status: 'planned',
        order_index: itinerary?.items?.length || 0
      })
      if (data.success) {
        setItinerary(prev => prev ? {
          ...prev,
          items: [...(prev.items || []), data.item]
        } : null)
        alert('Hotel added to itinerary successfully!')
        setShowHotelSearch(false)
      } else {
        alert('Failed to add hotel to itinerary')
      }
    } catch (error) {
      console.error('Failed to add hotel to itinerary:', error)
      alert('Failed to add hotel to itinerary')
    }
  }

  const addSavedEventToItinerary = async (event: any) => {
    try {
      const data = await apiClient.post(`/api/itineraries/${itineraryId}/items`, {
        item_type: 'event',
        title: event.title,
        description: event.venue || '',
        date: event.date || '',
        time: '',
        location: event.venue || '',
        price: event.price ? Number.parseFloat(event.price.replace(/[^0-9.]/g, '')) : 0,
        url: event.url || '',
        image_url: '',
        status: 'planned',
        order_index: itinerary?.items?.length || 0
      })
      if (data.success) {
        setItinerary(prev => prev ? {
          ...prev,
          items: [...(prev.items || []), data.item]
        } : null)
        alert('Event added to itinerary successfully!')
        setShowSavedEvents(false)
      } else {
        alert('Failed to add event to itinerary')
      }
    } catch (error) {
      console.error('Failed to add event to itinerary:', error)
      alert('Failed to add event to itinerary')
    }
  }

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = await apiClient.post(`/api/itineraries/${itineraryId}/items`, {
        ...newItem,
        price: newItem.price ? Number.parseFloat(newItem.price) : null,
        order_index: itinerary?.items?.length || 0
      })
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
      const data = await apiClient.delete(`/api/itineraries/${itineraryId}/items/${itemId}`)
      
      if (data.success) {
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

  const handleBudgetPreset = (amount: number) => {
    const current = Number.parseFloat(newBudget) || 0
    setNewBudget(Math.max(0, current + amount).toFixed(2))
  }

  const handleUpdateBudget = async () => {
    // Sanitize input like "1,200.50" → 1200.50 and prevent huge floats
    const sanitized = (newBudget || '').replace(/[^0-9.]/g, '')
    if (!sanitized || Number.isNaN(Number(sanitized))) {
      alert('Please enter a valid budget amount')
      return
    }

    try {
      const data = await apiClient.put(`/api/itineraries/${itineraryId}`, {
        budget: Number.parseFloat(Number.parseFloat(sanitized).toFixed(2))
      })
      if (data.success) {
        // After updating, refetch the itinerary to avoid any stale merges
        await fetchItinerary()
        setShowBudgetEdit(false)
        setNewBudget('')
        // no alert needed for simple UX
      } else {
        alert(data.error || 'Failed to update budget')
      }
    } catch (error) {
      console.error('Failed to update budget:', error)
      alert('Failed to update budget')
    }
  }

  // Helper functions to extract nested ternary operations
  const formatBudgetDisplay = (budget: number | null): string => {
    if (budget == null) return 'Not set'
    return `$${budget.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
  }

  const getBudgetStatusBadgeClass = (percentage: number): string => {
    if (percentage >= 100) return 'bg-red-500'
    if (percentage >= 80) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getBudgetStatusText = (percentage: number): string => {
    if (percentage >= 100) return 'Over Budget!'
    if (percentage >= 80) return 'Near Limit'
    return 'On Track'
  }

  // Reuse getBudgetStatusBadgeClass for progress bar color
  const getProgressBarColorClass = getBudgetStatusBadgeClass

  const getRemainingBudgetClass = (remaining: number): string => {
    return remaining >= 0 ? 'text-green-400' : 'text-red-400'
  }

  const formatRemainingBudget = (remaining: number): string => {
    if (remaining >= 0) {
      return `$${remaining.toLocaleString()} remaining`
    }
    return `$${Math.abs(remaining).toLocaleString()} over budget`
  }

  const getCategoryEmoji = (category: string): string => {
    if (category === 'hotel') return '🏨'
    if (category === 'event') return '🎵'
    if (category === 'flight') return '✈️'
    if (category === 'activity') return '🎯'
    return '📍'
  }

  const getStatusBadgeClass = (status: string): string => {
    if (status === 'draft') return 'bg-gray-500'
    if (status === 'active') return 'bg-green-500'
    if (status === 'completed') return 'bg-blue-500'
    return 'bg-red-500'
  }

  const getDailyBudgetBarColor = (percentage: number): string => {
    if (percentage >= 100) return 'bg-red-500'
    if (percentage >= 80) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const generateAIItinerary = async (customHints?: string) => {
    if (!itinerary) return
    if (!itinerary.destination || !itinerary.start_date || !itinerary.end_date) {
      alert('Destination and dates are required to generate an itinerary')
      return
    }
    setShowAIGenerateModal(false)
    setGeneratingAI(true)
    try {
      // 1) Fetch events for destination - filter by date range
      const startDate = itinerary.start_date
      const endDate = itinerary.end_date
      const eventsData = await apiClient.get(
        `/api/events?city=${encodeURIComponent(itinerary.destination)}&date_from=${startDate}&date_to=${endDate}&limit=50`
      )
      
      // Combine all event sources
      const allEvents = [
        ...(Array.isArray(eventsData?.ticketmaster) ? eventsData.ticketmaster : []),
        ...(Array.isArray(eventsData?.eventbrite) ? eventsData.eventbrite : []),
        ...(Array.isArray(eventsData?.csv_events) ? eventsData.csv_events : []),
        ...(Array.isArray(eventsData?.merged) ? eventsData.merged : [])
      ]
      
      // Remove duplicates and format for LLM
      const uniqueEvents = Array.from(
        new Map(allEvents.map(ev => [ev.id || ev.name, ev])).values()
      ).slice(0, 50)
      
      // Format events for LLM
      const events = uniqueEvents.map(ev => ({
        title: ev.name || ev.title || 'Untitled Event',
        date: ev.dates?.start?.localDate || ev.date || '',
        time: ev.dates?.start?.localTime || ev.time || '',
        venue: ev._embedded?.venues?.[0]?.name || ev.venue || 'TBA',
        city: ev._embedded?.venues?.[0]?.city?.name || ev.city || itinerary.destination,
        url: ev.url || '',
        description: ev.description || ''
      }))

      // 2) Fetch hotels via existing search proxy
      const hotelsResp = await fetch(`/api/hotels/search?city=${encodeURIComponent(itinerary.destination)}&limit=20`)
      const hotelsData = await hotelsResp.json()
      const hotels = Array.isArray(hotelsData?.hotels) ? hotelsData.hotels : []

      // 3) Call LLM itinerary generation
      const llmData = await apiClient.post('/api/llm/itinerary/generate', {
        destination: itinerary.destination,
        start_date: itinerary.start_date,
        end_date: itinerary.end_date,
        events,
        hotels,
        preferences: {
          budget: itinerary.budget,
          hints: customHints || aiHints || undefined,
          description: itinerary.description || undefined
        }
      })
      if (!llmData.success) {
        throw new Error(llmData.error || 'Failed to generate itinerary')
      }

      const plan = llmData.itinerary?.itinerary
      if (!Array.isArray(plan) || plan.length === 0) {
        alert('AI returned an empty plan')
        return
      }

      // Create a map of event titles to event data for matching
      const eventMap = new Map()
      uniqueEvents.forEach(ev => {
        const title = ev.name || ev.title || 'Untitled Event'
        eventMap.set(title.toLowerCase(), ev)
      })

      // Create a map of hotel names to hotel data
      const hotelMap = new Map()
      hotels.forEach(hotel => {
        const name = hotel.name || 'Unknown Hotel'
        hotelMap.set(name.toLowerCase(), hotel)
      })

      // 4) Persist generated items
      let addedCount = 0
      const addedHotels = new Set() // Track hotels to avoid duplicates

      for (const day of plan) {
        const dayDate = day.date || ''
        const hotelTitle = day.hotel || ''
        
        // Add hotel (only once per unique hotel)
        if (hotelTitle && !addedHotels.has(hotelTitle.toLowerCase())) {
          const hotelData = hotelMap.get(hotelTitle.toLowerCase()) || {}
          const hotelUrl = hotelData.url || ''
          const hotelAddress = hotelData.address || hotelData.location || ''
          const hotelPrice = hotelData.price_per_night ? 
            Number.parseFloat(String(hotelData.price_per_night).replace(/[^0-9.-]/g, '')) : null

          try {
            await apiClient.post(`/api/itineraries/${itineraryId}/items`, {
              item_type: 'hotel',
              title: hotelTitle,
              description: hotelAddress,
              date: dayDate,
              time: '15:00',
              location: hotelAddress,
              price: hotelPrice,
              url: hotelUrl,
              image_url: '',
              status: 'planned',
              order_index: addedCount++
            })
            addedHotels.add(hotelTitle.toLowerCase())
          } catch (e) {
            console.error('Failed to add hotel:', e)
          }
        }

        // Add events
        if (Array.isArray(day.events)) {
          for (const evTitle of day.events) {
            const title = typeof evTitle === 'string' ? evTitle : (evTitle?.title || '')
            const eventData = eventMap.get(title.toLowerCase()) || {}
            
            const eventDate = eventData.dates?.start?.localDate || eventData.date || dayDate
            const eventTime = eventData.dates?.start?.localTime || eventData.time || ''
            const eventVenue = eventData._embedded?.venues?.[0]?.name || eventData.venue || 'TBA'
            const eventUrl = eventData.url || ''
            const eventPrice = eventData.priceRanges?.[0]?.min || eventData.price || null

            try {
              await apiClient.post(`/api/itineraries/${itineraryId}/items`, {
                item_type: 'event',
                title,
                description: eventVenue,
                date: eventDate,
                time: eventTime,
                location: eventVenue,
                price: eventPrice,
                url: eventUrl,
                image_url: '',
                status: 'planned',
                order_index: addedCount++
              })
            } catch (e) {
              console.error('Failed to add event:', e)
            }
          }
        }

        // Add tips as notes
        if (day.tips) {
          try {
            await apiClient.post(`/api/itineraries/${itineraryId}/items`, {
              item_type: 'note',
              title: `Tips for Day ${day.day || ''}`.trim(),
              description: Array.isArray(day.tips) ? day.tips.join('\n') : String(day.tips),
              date: dayDate,
                time: '',
                location: '',
                price: null,
                url: '',
                image_url: '',
                status: 'planned',
                order_index: addedCount++
              })
          } catch (e) {
            console.error('Failed to add tips:', e)
          }
        }
      }

      await fetchItinerary()
      alert('AI itinerary generated and added to your plan!')
    } catch (e: any) {
      console.error('AI generation failed:', e)
      alert(e?.message || 'Failed to generate itinerary')
    } finally {
      setGeneratingAI(false)
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

  // Budget calculations
  const calculateBudgetStats = () => {
    if (!itinerary?.items) return { totalSpent: 0, categories: {}, percentage: 0, remaining: 0 }
    
    const totalSpent = itinerary.items.reduce((sum, item) => sum + (item.price || 0), 0)
    const categories = itinerary.items.reduce((acc, item) => {
      const category = item.item_type
      if (!acc[category]) acc[category] = 0
      acc[category] += item.price || 0
      return acc
    }, {} as Record<string, number>)
    
    const percentage = itinerary.budget ? (totalSpent / itinerary.budget) * 100 : 0
    const remaining = itinerary.budget ? itinerary.budget - totalSpent : 0
    
    return { totalSpent, categories, percentage, remaining }
  }

  const generateCSV = () => {
    if (!itinerary) return ''
    
    const headers = ['Item Type', 'Title', 'Description', 'Date', 'Time', 'Location', 'Price', 'URL']
    const rows = itinerary.items?.map(item => [
      item.item_type,
      item.title,
      item.description || '',
      item.date || '',
      item.time || '',
      item.location || '',
      item.price || 0,
      item.url || ''
    ]) || []
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n')
    
    return csvContent
  }

  const downloadCSV = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
  }

  // Recompute budget stats for rendering below
  const budgetStats = calculateBudgetStats()

  // Per-day budget breakdown
  const dailyBreakdown = useMemo(() => {
    const byDate: Record<string, { items: typeof sortedItems; total: number }> = {}
    for (const item of sortedItems) {
      const key = item.date ? new Date(item.date).toISOString().slice(0, 10) : 'No date'
      if (!byDate[key]) byDate[key] = { items: [], total: 0 }
      byDate[key].items.push(item)
      byDate[key].total += item.price || 0
    }
    return Object.entries(byDate)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, data]) => ({ date, ...data }))
  }, [sortedItems])

  // Derive number of days in itinerary window if dates available
  const itineraryDaySpan = useMemo(() => {
    if (!itinerary?.start_date || !itinerary?.end_date) return null
    const start = new Date(itinerary.start_date)
    const end = new Date(itinerary.end_date)
    const diff = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1
    return diff > 0 ? diff : null
  }, [itinerary?.start_date, itinerary?.end_date])

  // Show loading state while authentication is being checked
  if (loading && !itinerary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-xl">Loading travel plan...</p>
        </div>
      </div>
    )
  }

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
            <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium text-white ${getStatusBadgeClass(itinerary.status)}`}>
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
                {formatBudgetDisplay(itinerary.budget)}
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

        {/* Budget Management Section */}
        {itinerary.budget && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">💰 Budget Overview</h2>
              <div className="flex gap-3 items-center">
                <button
                  onClick={() => setShowExportModal(true)}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors"
                >
                  📊 Export CSV
                </button>
                <button
                  onClick={() => {
                    setNewBudget(itinerary.budget != null ? itinerary.budget.toFixed(2) : '')
                    setShowBudgetEdit(true)
                  }}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                >
                  ✏️ Edit Budget
                </button>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getBudgetStatusBadgeClass(budgetStats.percentage)}`}>
                  {getBudgetStatusText(budgetStats.percentage)}
                </div>
              </div>
            </div>

            {/* Budget Progress Bar */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-300">Spent: ${budgetStats.totalSpent.toLocaleString()}</span>
                <span className="text-sm text-gray-300">Budget: ${itinerary.budget.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all duration-500 ${getProgressBarColorClass(budgetStats.percentage)}`}
                  style={{ width: `${Math.min(budgetStats.percentage, 100)}%` }}
                ></div>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm text-gray-400">
                  {budgetStats.percentage.toFixed(1)}% used
                </span>
                <span className={`text-sm font-medium ${getRemainingBudgetClass(budgetStats.remaining)}`}>
                  {formatRemainingBudget(budgetStats.remaining)}
                </span>
              </div>
            </div>

            {/* Budget Breakdown by Category */}
            {Object.keys(budgetStats.categories).length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-300 mb-4">Spending by Category</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(budgetStats.categories).map(([category, amount]) => (
                    <div key={category} className="bg-gray-700/50 p-4 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">
                          {getCategoryEmoji(category)}
                        </span>
                        <span className="font-medium capitalize">{category}</span>
                      </div>
                      <div className="text-xl font-bold text-green-400">
                        ${amount.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-400">
                        {((amount / budgetStats.totalSpent) * 100).toFixed(1)}% of total
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Add Item Buttons */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Itinerary Items</h2>
          <div className="flex gap-3">
            <button
              onClick={() => setShowAIGenerateModal(true)}
              disabled={generatingAI}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-2 rounded-lg"
            >
              {generatingAI ? 'Generating…' : '✨ Generate with AI'}
            </button>
            <button
              onClick={() => setShowHotelSearch(true)}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
            >
              🏨 Add Hotels
            </button>
            <button
              onClick={() => setShowSavedEvents(true)}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg"
            >
              📅 Add from Saved Events ({savedEvents.length})
            </button>
            <button
              onClick={() => setShowAddItemForm(true)}
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg"
            >
              + Add Custom Item
            </button>
          </div>
        </div>

        {/* Add Item Form */}
        {showAddItemForm && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <h3 className="text-xl font-bold mb-4">Add New Item</h3>
            <form onSubmit={handleAddItem} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="item_type" className="block text-sm font-medium mb-2">Type *</label>
                  <select
                    id="item_type"
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
                  <label htmlFor="item_title" className="block text-sm font-medium mb-2">Title *</label>
                  <input
                    id="item_title"
                    type="text"
                    value={newItem.title}
                    onChange={(e) => setNewItem({...newItem, title: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="item_date" className="block text-sm font-medium mb-2">Date</label>
                  <input
                    id="item_date"
                    type="date"
                    value={newItem.date}
                    onChange={(e) => setNewItem({...newItem, date: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="item_time" className="block text-sm font-medium mb-2">Time</label>
                  <input
                    id="item_time"
                    type="time"
                    value={newItem.time}
                    onChange={(e) => setNewItem({...newItem, time: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="item_location" className="block text-sm font-medium mb-2">Location</label>
                  <input
                    id="item_location"
                    type="text"
                    value={newItem.location}
                    onChange={(e) => setNewItem({...newItem, location: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="item_price" className="block text-sm font-medium mb-2">Price ($)</label>
                  <input
                    id="item_price"
                    type="number"
                    step="0.01"
                    value={newItem.price}
                    onChange={(e) => setNewItem({...newItem, price: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="item_description" className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  id="item_description"
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

        {/* Saved Events Selection */}
        {showSavedEvents && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Select from Your Saved Events</h3>
              <button
                onClick={() => setShowSavedEvents(false)}
                className="text-gray-400 hover:text-gray-300"
              >
                ✕ Close
              </button>
            </div>
            
            {savedEvents.length === 0 ? (
              <p className="text-gray-400 text-center py-4">No saved events yet. Go to the main page and save some events!</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedEvents.map((event) => (
                  <div key={event.id || event.title || `event-${event.url}`} className="bg-gray-700/50 p-4 rounded-lg hover:bg-gray-600/50 transition-colors">
                    <h4 className="font-semibold mb-2">{event.title}</h4>
                    {event.venue && <p className="text-sm text-gray-300 mb-2">📍 {event.venue}</p>}
                    {event.date && <p className="text-sm text-gray-300 mb-2">📅 {event.date}</p>}
                    {event.price && <p className="text-sm text-green-400 mb-3">💰 {event.price}</p>}
                    <div className="flex gap-2">
                      <button
                        onClick={() => addSavedEventToItinerary(event)}
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm flex-1"
                      >
                        Add to Itinerary
                      </button>
                      <a
                        href={event.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm"
                      >
                        View
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Hotel Search */}
        {showHotelSearch && (
          <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Search Hotels</h3>
              <button
                onClick={() => setShowHotelSearch(false)}
                className="text-gray-400 hover:text-gray-300"
              >
                ✕ Close
              </button>
            </div>
            
            <div className="mb-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={hotelSearchCity}
                  onChange={(e) => setHotelSearchCity(e.target.value)}
                  placeholder="Enter city name (e.g., Toronto, Mumbai)"
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={searchHotels}
                  disabled={hotelSearchLoading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded-lg"
                >
                  {hotelSearchLoading ? 'Searching...' : '🔍 Search'}
                </button>
              </div>
            </div>
            
            {hotelSearchLoading && (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="mt-2 text-gray-400">Searching hotels...</p>
              </div>
            )}
            
            {!hotelSearchLoading && hotelSearchResults.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {hotelSearchResults.map((hotel) => (
                  <div key={hotel.id || hotel.name || hotel.url || `hotel-${hotel.address}`} className="bg-gray-700/50 p-4 rounded-lg hover:bg-gray-600/50 transition-colors">
                    <h4 className="font-semibold mb-2">{hotel.name}</h4>
                    {hotel.address && <p className="text-sm text-gray-300 mb-2">📍 {hotel.address}</p>}
                    {hotel.city && <p className="text-sm text-gray-300 mb-2">🏙️ {hotel.city}</p>}
                    {hotel.rating && <p className="text-sm text-yellow-400 mb-2">⭐ {hotel.rating}/10</p>}
                    {hotel.price_per_night && <p className="text-sm text-green-400 mb-3">💰 {hotel.price_per_night}</p>}
                    <div className="flex gap-2">
                      <button
                        onClick={() => addHotelToItinerary(hotel)}
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm flex-1"
                      >
                        Add to Itinerary
                      </button>
                      {hotel.url && (
                        <a
                          href={hotel.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm"
                        >
                          View
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {!hotelSearchLoading && hotelSearchResults.length === 0 && hotelSearchCity && (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🏨</div>
                <p className="text-gray-400">No hotels found for "{hotelSearchCity}"</p>
                <p className="text-gray-500 text-sm mt-2">Try searching for a different city</p>
              </div>
            )}
            
            {!hotelSearchLoading && !hotelSearchCity && (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🔍</div>
                <p className="text-gray-400">Enter a city name to search for hotels</p>
              </div>
            )}
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
            {/* Per-day budget breakdown */}
            {dailyBreakdown.length > 0 && (
              <div className="bg-gray-800/50 p-6 rounded-lg">
                <h3 className="text-xl font-bold mb-4">Per-day Budget</h3>
                <div className="space-y-4">
                  {dailyBreakdown.map((day) => {
                    const dayTotal = day.total
                    const divisor = itineraryDaySpan || dailyBreakdown.length
                    const dailyBudget = itinerary?.budget ? itinerary.budget / Math.max(1, divisor) : 0
                    const pct = dailyBudget ? Math.min(100, (dayTotal / dailyBudget) * 100) : 0
                    const barColor = getDailyBudgetBarColor(pct)
                    return (
                      <div key={day.date} className="border border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-semibold">{day.date === 'No date' ? 'No date' : new Date(day.date).toLocaleDateString()}</div>
                          <div className="text-sm text-gray-300">
                            ${dayTotal.toLocaleString()} {dailyBudget ? `of $${dailyBudget.toFixed(2)}` : ''}
                          </div>
                        </div>
                        {dailyBudget > 0 && (
                          <div className="h-2 bg-gray-700 rounded">
                            <div className={`h-2 ${barColor} rounded`} style={{ width: `${pct}%` }} />
                          </div>
                        )}
                        {/* Items list for the day */}
                        <div className="mt-3 space-y-2">
                          {day.items.map((i) => (
                            <div key={i.id} className="text-sm text-gray-300 flex justify-between">
                              <span>
                                <span className="mr-2">{getItemTypeIcon(i.item_type)}</span>
                                {i.title}
                              </span>
                              {i.price ? (
                                <span className="text-green-400">${i.price.toLocaleString()}</span>
                              ) : (
                                <span className="text-gray-500">—</span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

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

        {/* Budget Edit Modal */}
        {showBudgetEdit && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Edit Budget</h2>
                  <button
                    onClick={() => setShowBudgetEdit(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>

                <div className="mb-6">
                  <label htmlFor="budget_amount" className="block text-sm font-medium text-gray-700 mb-2">
                    Budget Amount ($)
                  </label>
                  <input
                    id="budget_amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={newBudget}
                    onChange={(e) => setNewBudget(e.target.value)}
                    placeholder="Enter budget amount"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-gray-900 placeholder-gray-400"
                  />
                  {/* Quick Preset Buttons */}
                  <div className="mt-3 grid grid-cols-4 gap-2">
                    <button
                      type="button"
                      onClick={() => handleBudgetPreset(-100)}
                      className="px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded border"
                    >
                      -$100
                    </button>
                    <button
                      type="button"
                      onClick={() => handleBudgetPreset(-50)}
                      className="px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded border"
                    >
                      -$50
                    </button>
                    <button
                      type="button"
                      onClick={() => handleBudgetPreset(50)}
                      className="px-2 py-1 bg-green-100 hover:bg-green-200 text-green-700 text-sm rounded border"
                    >
                      +$50
                    </button>
                    <button
                      type="button"
                      onClick={() => handleBudgetPreset(100)}
                      className="px-2 py-1 bg-green-100 hover:bg-green-200 text-green-700 text-sm rounded border"
                    >
                      +$100
                    </button>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handleUpdateBudget}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Update Budget
                  </button>
                  <button
                    onClick={() => setShowBudgetEdit(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Export CSV Modal */}
        {showExportModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Export Itinerary</h2>
                  <button
                    onClick={() => setShowExportModal(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>

                <div className="mb-6">
                  <p className="text-gray-600 mb-4">Download your itinerary as a CSV file with all items and costs.</p>
                  <button
                    onClick={() => {
                      const csvContent = generateCSV()
                      downloadCSV(csvContent, `${itinerary.title.replace(/[^a-z0-9]/gi, '_')}_itinerary.csv`)
                      setShowExportModal(false)
                    }}
                    className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    📊 Download CSV
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Generate Modal with Hints */}
        {showAIGenerateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">✨ Generate AI Itinerary</h2>
                  <button
                    onClick={() => setShowAIGenerateModal(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>

                <div className="mb-6">
                  <p className="text-gray-600 mb-4">
                    The AI will use your travel plan details (destination, dates, budget) and available events/hotels to create a personalized itinerary.
                  </p>
                  
                  <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">📋 What the AI knows:</h3>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• <strong>Destination:</strong> {itinerary.destination || 'Not set'}</li>
                      <li>• <strong>Dates:</strong> {itinerary.start_date} to {itinerary.end_date}</li>
                      <li>• <strong>Budget:</strong> ${itinerary.budget?.toLocaleString() || 'Not set'}</li>
                      <li>• <strong>Available Events:</strong> Will fetch events for your destination and dates</li>
                      <li>• <strong>Available Hotels:</strong> Will fetch hotels for your destination</li>
                    </ul>
                  </div>

                  <div className="mb-4">
                    <label htmlFor="ai_hints" className="block text-sm font-medium text-gray-700 mb-2">
                      💡 Additional Hints/Instructions (Optional)
                    </label>
                    <textarea
                      id="ai_hints"
                      value={aiHints}
                      onChange={(e) => setAiHints(e.target.value)}
                      placeholder="E.g., 'Focus on music events', 'Prefer budget-friendly hotels', 'Include outdoor activities', 'I love art museums', 'Avoid crowded tourist spots'..."
                      rows={5}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-gray-900 placeholder-gray-400"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Provide any preferences, interests, or special requirements to help the AI create a better itinerary for you.
                    </p>
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => generateAIItinerary(aiHints)}
                      className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors font-semibold"
                    >
                      ✨ Generate Itinerary
                    </button>
                    <button
                      onClick={() => {
                        setShowAIGenerateModal(false)
                        setAiHints('')
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
