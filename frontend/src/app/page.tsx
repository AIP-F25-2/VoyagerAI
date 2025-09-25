'use client'

import { useState, useEffect } from 'react'

interface Event {
  id: number
  title: string
  date: string | null
  time: string | null
  venue: string | null
  place: string | null
  price: string | null
  url: string | null
  city: string | null
  created_at: string
}

export default function Home() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [city, setCity] = useState('Mumbai')
  const [limit, setLimit] = useState(10)

  const fetchEvents = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:5000/api/events')
      const data = await response.json()
      if (data.success) {
        setEvents(data.events)
      }
    } catch (error) {
      console.error('Error fetching events:', error)
    } finally {
      setLoading(false)
    }
  }

  const scrapeEvents = async () => {
    try {
      setScraping(true)
      const response = await fetch('http://localhost:5000/api/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city: city,
          limit: limit
        })
      })
      const data = await response.json()
      if (data.success) {
        alert(`Scraped ${data.scraped_count} events, saved ${data.saved_count} new events`)
        fetchEvents() // Refresh the events list
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Error scraping events:', error)
      alert('Error scraping events')
    } finally {
      setScraping(false)
    }
  }

  useEffect(() => {
    fetchEvents()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">
          🚀 VoyagerAI Events
        </h1>
        
        {/* Scraping Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Scrape Events</h2>
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City
              </label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter city name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Limit
              </label>
              <input
                type="number"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="50"
              />
            </div>
            <button
              onClick={scrapeEvents}
              disabled={scraping}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {scraping ? 'Scraping...' : 'Scrape Events'}
            </button>
            <button
              onClick={fetchEvents}
              disabled={loading}
              className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Events List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4">
            Events ({events.length})
          </h2>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading events...</p>
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600">No events found. Try scraping some events!</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {events.map((event) => (
                <div key={event.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-800 mb-2">
                        {event.title}
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                        {event.date && (
                          <p><span className="font-medium">Date:</span> {event.date}</p>
                        )}
                        {event.time && (
                          <p><span className="font-medium">Time:</span> {event.time}</p>
                        )}
                        {event.venue && (
                          <p><span className="font-medium">Venue:</span> {event.venue}</p>
                        )}
                        {event.place && (
                          <p><span className="font-medium">Place:</span> {event.place}</p>
                        )}
                        {event.price && (
                          <p><span className="font-medium">Price:</span> {event.price}</p>
                        )}
                        {event.city && (
                          <p><span className="font-medium">City:</span> {event.city}</p>
                        )}
                      </div>
                    </div>
                    {event.url && (
                      <a
                        href={event.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                      >
                        View Event
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}