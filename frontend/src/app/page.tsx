'use client'

import { useState, useEffect, useRef } from 'react'
import styles from './page.module.css'
import { EventItem, fetchEvents, getAdaptiveRefreshIntervalMs } from '@/lib/api'
import EventCard from '@/components/EventCard'
import SkeletonCard from '@/components/SkeletonCard'
import HotelsPlanner from '@/components/HotelsPlanner'
import Header from '@/components/Header'

export default function Home() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [loading, setLoading] = useState(true)
  const [city, setCity] = useState('Mumbai')
  const [limit, setLimit] = useState(10)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const load = async () => {
    try {
      setLoading(true)
      const data = await fetchEvents(city, limit)
      setEvents(data)
    } catch (error) {
      console.error('Error fetching events:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const start = async () => {
      await load()
      const latest = events[0]?.created_at
      const interval = getAdaptiveRefreshIntervalMs(latest)
      if (timerRef.current) clearInterval(timerRef.current)
      timerRef.current = setInterval(load, interval)
    }
    void start()
    const onFocus = () => { void load() }
    window.addEventListener('focus', onFocus)
    return () => {
      window.removeEventListener('focus', onFocus)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onApplyFilters = async () => {
    await load()
  }


  return (
    <div className={styles.page}>
      <Header />
      <section className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.dot}></span>
          Live events feed
        </div>
        <h1 className={styles.heroTitle}>Discover events with VoyagerAI</h1>
        <p className={styles.heroDesc}>
          Explore the latest happenings across cities. Filter by city and limit, then jump straight to event pages.
        </p>
      </section>

      <section className={`${styles.card} ${styles.cardPad}`}>
        <div className={styles.listHeader}>
          <h2>Events ({events.length})</h2>
          {!loading && (
            <span className={styles.subtle}>Auto-updating</span>
          )}
        </div>

        <div className={styles.controls}>
          <label className={styles.controlGroup}>
            <span>City</span>
            <input className={styles.input} value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g., Mumbai" />
          </label>
          <label className={styles.controlGroup}>
            <span>Limit</span>
            <input className={`${styles.input} ${styles.inputSmall}`} type="number" min={1} max={100} value={limit} onChange={(e) => setLimit(parseInt(e.target.value || '10'))} />
          </label>
          <div style={{ display: 'flex', gap: '.5rem', marginLeft: 'auto' }}>
            <button className={styles.primaryBtn} onClick={onApplyFilters} disabled={loading}>Apply</button>
          </div>
        </div>

        {loading ? (
          <div className={styles.grid}>
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className={styles.emptyWrap}>
            <div className={styles.emptyIcon}><div className={styles.emptyDot}></div></div>
            <h3 className="mt-4">No events yet</h3>
            <p className="text-neutral-600 dark:text-neutral-400">Waiting for new events…</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>

      <HotelsPlanner />
    </div>
  )
}