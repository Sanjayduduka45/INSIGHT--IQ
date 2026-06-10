import React, { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from './supabase'

interface User {
  id: string
  email: string
  role: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isMock: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => void
  resetPassword: (email: string) => Promise<void>
  continueAsGuest: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || ''
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
const isMock = !SUPABASE_URL || !SUPABASE_ANON_KEY

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (isMock) {
      const storedUser = localStorage.getItem('insightiq_user')
      const storedToken = localStorage.getItem('insightiq_token')

      if (storedUser && storedToken) {
        setUser(JSON.parse(storedUser))
        setToken(storedToken)
      }
      setIsLoading(false)
      return
    }

    // Load active session from Supabase
    supabase.auth.getSession().then(({ data: { session } }: any) => {
      if (session) {
        const activeUser = {
          id: session.user.id,
          email: session.user.email || '',
          role: session.user.role || 'user',
        }
        setUser(activeUser)
        setToken(session.access_token)
        localStorage.setItem('insightiq_user', JSON.stringify(activeUser))
        localStorage.setItem('insightiq_token', session.access_token)
      }
      setIsLoading(false)
    })

    // Listen for auth state changes to keep session refreshed
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: any, session: any) => {
      if (session) {
        const activeUser = {
          id: session.user.id,
          email: session.user.email || '',
          role: session.user.role || 'user',
        }
        setUser(activeUser)
        setToken(session.access_token)
        localStorage.setItem('insightiq_user', JSON.stringify(activeUser))
        localStorage.setItem('insightiq_token', session.access_token)
      } else {
        setUser(null)
        setToken(null)
        localStorage.removeItem('insightiq_user')
        localStorage.removeItem('insightiq_token')
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const login = async (email: string, password: string) => {
    if (isMock) {
      await new Promise((resolve) => setTimeout(resolve, 800))
      if (password.length < 6) {
        throw new Error('Password must be at least 6 characters.')
      }
      const mockUser = {
        id: 'mock-user-id-' + Math.random().toString(36).substr(2, 9),
        email,
        role: 'user',
      }
      const mockToken = 'mock-jwt-token-for-dev-environment'
      setUser(mockUser)
      setToken(mockToken)
      localStorage.setItem('insightiq_user', JSON.stringify(mockUser))
      localStorage.setItem('insightiq_token', mockToken)
      return
    }

    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      const msg = error.message.toLowerCase()
      if (msg.includes('invalid login credentials') || msg.includes('invalid credentials')) {
        throw new Error('Invalid email or password. Please try again.')
      } else if (msg.includes('email not confirmed')) {
        throw new Error('Please confirm your email address before signing in.')
      }
      throw new Error(error.message)
    }

    if (data.session && data.user) {
      const activeUser = {
        id: data.user.id,
        email: data.user.email || '',
        role: data.user.role || 'user',
      }
      setUser(activeUser)
      setToken(data.session.access_token)
      localStorage.setItem('insightiq_user', JSON.stringify(activeUser))
      localStorage.setItem('insightiq_token', data.session.access_token)
    }
  }

  const signup = async (email: string, password: string) => {
    if (isMock) {
      await new Promise((resolve) => setTimeout(resolve, 800))
      if (password.length < 6) {
        throw new Error('Password must be at least 6 characters.')
      }
      const mockUser = {
        id: 'mock-user-id-' + Math.random().toString(36).substr(2, 9),
        email,
        role: 'user',
      }
      const mockToken = 'mock-jwt-token-for-dev-environment'
      setUser(mockUser)
      setToken(mockToken)
      localStorage.setItem('insightiq_user', JSON.stringify(mockUser))
      localStorage.setItem('insightiq_token', mockToken)
      return
    }

    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) {
      const msg = error.message.toLowerCase()
      if (msg.includes('already registered') || msg.includes('already exists') || msg.includes('user already exists')) {
        throw new Error('This email is already registered. Please sign in instead.')
      } else if (msg.includes('weak') || msg.includes('should be at least') || msg.includes('password should be')) {
        throw new Error('Password is too weak. It must be at least 6 characters.')
      } else if (msg.includes('invalid email')) {
        throw new Error('Please enter a valid email address.')
      }
      throw new Error(error.message)
    }

    if (data.session && data.user) {
      const activeUser = {
        id: data.user.id,
        email: data.user.email || '',
        role: data.user.role || 'user',
      }
      setUser(activeUser)
      setToken(data.session.access_token)
      localStorage.setItem('insightiq_user', JSON.stringify(activeUser))
      localStorage.setItem('insightiq_token', data.session.access_token)
    } else if (data.user) {
      // Supabase signUp succeeded but requires email confirmation
      if (data.user.identities && data.user.identities.length === 0) {
        throw new Error('This email is already registered. Please sign in instead.')
      }
      throw new Error('CONFIRM_EMAIL_REQUIRED')
    } else {
      throw new Error('Signup succeeded, but no session was created. Please try logging in.')
    }
  }

  const continueAsGuest = () => {
    const guestUser = {
      id: 'guest-user-session',
      email: 'guest@insightiq.internal',
      role: 'guest',
    }
    const guestToken = 'guest-jwt-token'
    setUser(guestUser)
    setToken(guestToken)
    localStorage.setItem('insightiq_user', JSON.stringify(guestUser))
    localStorage.setItem('insightiq_token', guestToken)
  }

  const logout = async () => {
    if (!isMock) {
      await supabase.auth.signOut()
    }
    setUser(null)
    setToken(null)
    localStorage.removeItem('insightiq_user')
    localStorage.removeItem('insightiq_token')
  }

  const resetPassword = async (email: string) => {
    if (isMock) {
      await new Promise((resolve) => setTimeout(resolve, 800))
      return
    }
    const { error } = await supabase.auth.resetPasswordForEmail(email)
    if (error) {
      const msg = error.message.toLowerCase()
      if (msg.includes('user not found')) {
        throw new Error('Account not found for this email address.')
      }
      throw new Error(error.message)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isMock,
        login,
        signup,
        logout,
        resetPassword,
        continueAsGuest,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
