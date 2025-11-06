'use client'

import AuthForm from '@/components/AuthForm'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import styles from '../page.module.css'

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  
  const onSubmit = async (email: string, password: string) => {
    const res = await login(email, password)
    if (!res.success) {
      throw new Error(res.message || 'Invalid credentials')
    }
    // Redirect to home page after successful login
    router.push('/')
  }

  return (
    <div className={styles.authBg}>
      <div className={`${styles.card} ${styles.cardPad}`}>
        <AuthForm mode="login" onSubmit={onSubmit} />
      </div>
    </div>
  )
}



