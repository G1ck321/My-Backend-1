/**
 * TokenManager - Secure token storage and retrieval
 * For web: localStorage (SPA); for native mobile: migrate to secure storage
 */
const TokenManager = {
  ACCESS_TOKEN_KEY: 'fb_access_token',
  REFRESH_TOKEN_KEY: 'fb_refresh_token',
  USER_KEY: 'fb_user',

  getAccessToken() {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY)
  },

  setAccessToken(token) {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, token)
  },

  clearAccessToken() {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY)
  },

  getRefreshToken() {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  },

  setRefreshToken(token) {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token)
  },

  clearRefreshToken() {
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY)
    return raw ? JSON.parse(raw) : null
  },

  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user))
  },

  clearUser() {
    localStorage.removeItem(this.USER_KEY)
  },

  logout() {
    this.clearAccessToken()
    this.clearRefreshToken()
    this.clearUser()
  },

  isAuthenticated() {
    return !!this.getAccessToken()
  },
}

/**
 * FetchWithAuth - Wrapper around fetch that auto-includes JWT
 * Handles token refresh on 401
 */
async function fetchWithAuth(url, options = {}) {
  const token = TokenManager.getAccessToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    const refreshToken = TokenManager.getRefreshToken()

    if (refreshToken) {
      try {
        const refreshResponse = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refreshToken }),
        })

        if (refreshResponse.ok) {
          const { data } = await refreshResponse.json()
          TokenManager.setAccessToken(data.accessToken)
          headers.Authorization = `Bearer ${data.accessToken}`

          response = await fetch(url, {
            ...options,
            headers,
          })
        } else {
          TokenManager.logout()
          window.location.href = '/public/login.html'
          return
        }
      } catch (error) {
        TokenManager.logout()
        window.location.href = '/public/login.html'
        return
      }
    } else {
      TokenManager.logout()
      window.location.href = '/public/login.html'
      return
    }
  }

  return response
}

/**
 * PageGuard - Redirect unauthenticated users to login
 */
function requireAuth() {
  if (!TokenManager.isAuthenticated()) {
    window.location.href = '/public/login.html'
  }
}

/**
 * Check if user is authenticated and redirect if so
 */
function redirectIfAuthenticated() {
  if (TokenManager.isAuthenticated()) {
    window.location.href = '/public/menu.html'
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TokenManager, fetchWithAuth, requireAuth, redirectIfAuthenticated }
}
