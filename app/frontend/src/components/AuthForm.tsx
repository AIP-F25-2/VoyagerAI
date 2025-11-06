'use client'

import { useState } from 'react'
import Link from 'next/link'
import styles from './AuthForm.module.css'

export interface AuthFormProps {
  mode: 'login' | 'signup'
  onSubmit: (email: string, password: string, name?: string) => Promise<void>
}

export default function AuthForm({ mode, onSubmit }: AuthFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const title = mode === 'login' ? 'Welcome back' : 'Create your account'
  const subtitle = mode === 'login' ? 'Sign in to continue' : 'Join VoyagerAI to explore more'
  const buttonText = mode === 'login' ? 'Log in' : 'Sign up'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    // basic client-side validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setLoading(true)
    try {
      await onSubmit(email, password, mode === 'signup' ? name : undefined)
      setSuccess(mode === 'login' ? 'Logged in successfully.' : 'Account created successfully.')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Something went wrong.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={`${styles.card} ${styles.pad}`}>
        <div className={styles.glow} />
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.subtitle}>{subtitle}</p>

        {error && <div className={styles.error}>{error}</div>}
        {success && <div className={styles.success}>{success}</div>}

        <form className={styles.form} onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <label>
              <span className={styles.label}>Name</span>
              <input className={styles.input} value={name} onChange={e => setName(e.target.value)} placeholder="Your name" required />
            </label>
          )}
          <label>
            <span className={styles.label}>Email</span>
            <input className={styles.input} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
          </label>
          <label>
            <span className={styles.label}>Password</span>
            <div className={styles.inputRow}>
              <input className={styles.input} type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
              <button type="button" className={styles.toggle} onClick={() => setShowPassword(v => !v)}>{showPassword ? 'Hide' : 'Show'}</button>
            </div>
          </label>

          <div className={styles.actions}>
            <button className={styles.primary} type="submit" disabled={loading}>{loading ? 'Please wait…' : buttonText}</button>
          </div>

          <div className={styles.divider}>or continue with</div>
          <div className={styles.socialRow}>
            <button type="button" className={styles.socialBtn}><span className={styles.icon} /> Google</button>
            <button type="button" className={styles.socialBtn}><span className={styles.icon} /> GitHub</button>
          </div>

          <div className={styles.helperRow}>
            {mode === 'login' ? (
              <span className={styles.hint}>No account? <Link className={styles.helperLink} href="/signup">Sign up</Link></span>
            ) : (
              <span className={styles.hint}>Already have an account? <Link className={styles.helperLink} href="/login">Log in</Link></span>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}



