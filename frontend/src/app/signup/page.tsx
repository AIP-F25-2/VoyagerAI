'use client'

import AuthForm from '@/components/AuthForm'
import { signup } from '@/lib/api'
import styles from '../page.module.css'

export default function SignupPage() {
  const onSubmit = async (email: string, password: string, name?: string) => {
    const res = await signup(name || '', email, password)
    if (!res.success) {
      throw new Error(res.message || 'Could not create account')
    }
    // In a real app, store token and redirect
    // localStorage.setItem('token', res.token || '')
  }

  return (
    <div className={styles.authBg}>
      <div className={`${styles.card} ${styles.cardPad}`}>
        <AuthForm mode="signup" onSubmit={onSubmit} />
      </div>
    </div>
  )
}



