import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { authLogin, authMe, authRegister, clearToken, getToken, setToken } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    localStorage.removeItem('jeevakosha_user')
    localStorage.removeItem('jeevakosha_users')
  }, [])

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    authMe()
      .then(u => setUser(u))
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const { access_token, user: u } = await authLogin(email, password)
    setToken(access_token)
    setUser(u)
  }, [])

  const signup = useCallback(async (name, email, password) => {
    const { access_token, user: u } = await authRegister(name, email, password)
    setToken(access_token)
    setUser(u)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
