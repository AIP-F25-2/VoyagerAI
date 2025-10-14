'use client'

import AuthForm from '@/components/AuthForm'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import styles from '../page.module.css'

export default function SignupPage() {
  const { signup } = useAuth()
  const router = useRouter()
  
  const onSubmit = async (email: string, password: string, name?: string) => {
    const res = await signup(name || '', email, password)
    if (!res.success) {
      throw new Error(res.message || 'Could not create account')
    }
    // Redirect to home page after successful signup
    router.push('/')
  }

  return (
    <div className={styles.authBg}>
      <div className={`${styles.card} ${styles.cardPad}`}>
        <AuthForm mode="signup" onSubmit={onSubmit} />
      </div>
    </div>
  )
}



