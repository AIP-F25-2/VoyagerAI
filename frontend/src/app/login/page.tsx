'use client'

import AuthForm from '@/components/AuthForm'
import { login } from '@/lib/api'
import styles from '../page.module.css'

export default function LoginPage() {
  const onSubmit = async (email: string, password: string) => {
    const res = await login(email, password)
    if (!res.success) {
      throw new Error(res.message || 'Invalid credentials')
    }
    // In a real app, store token and redirect
    // localStorage.setItem('token', res.token || '')
  }

  return (
    <div className={styles.authBg}>
      <div className={`${styles.card} ${styles.cardPad}`}>
        <AuthForm mode="login" onSubmit={onSubmit} />
      </div>
    </div>
  )
}



