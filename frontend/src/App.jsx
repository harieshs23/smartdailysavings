import { useState, useEffect } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''
const AUTH_TOKEN_KEY = 'smartdailysavings_token'

const defaultDeals = [
  { platform: 'BigBasket', title: 'Fortune Sunlite Refined Sunflower Oil 5L', price: '₹549', mrp: '₹620', discount: '54% OFF', votes: 143, category: 'Groceries', isNew: true },
  { platform: '1mg', title: 'Metformin 500mg Generic — 60 tablets', price: '₹38', mrp: '₹245', discount: 'GENERIC', votes: 89, category: 'Medicine' },
  { platform: 'Flipkart', title: 'boAt Airdopes 141 True Wireless Earbuds', price: '₹899', mrp: '₹1,499', discount: '40% OFF', votes: 312, category: 'Electronics' },
  { platform: 'Meesho', title: 'Cotton Solid Baseball Cap — Unisex', price: '₹129', mrp: '₹399', discount: '67% OFF', votes: 204, category: 'Fashion' },
  { platform: 'Amazon', title: 'Prestige Omega Deluxe Granite Cookware Set', price: '₹1,799', mrp: '₹2,999', discount: '40% OFF', votes: 451, category: 'Home & Kitchen', isNew: true },
]

const categories = ['All', 'Groceries', 'Medicine', 'Electronics', 'Fashion', 'Home & Kitchen']

function App() {
  const [email, setEmail] = useState('')
  const [query, setQuery] = useState('iphone')
  const [category, setCategory] = useState('All')
  const [deals, setDeals] = useState(defaultDeals)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [authMode, setAuthMode] = useState('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authName, setAuthName] = useState('')
  const [authUser, setAuthUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [showAuthDrawer, setShowAuthDrawer] = useState(false)
  const [showVerification, setShowVerification] = useState(false)
  const [verificationEmail, setVerificationEmail] = useState('')
  const [verificationMessage, setVerificationMessage] = useState('')
  const [region, setRegion] = useState('')

  useEffect(() => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    if (!token) return

    fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Session expired')
        const data = await res.json()
        setAuthUser(data.user)
      })
      .catch(() => {
        localStorage.removeItem(AUTH_TOKEN_KEY)
      })
  }, [])

  // Check for email verification token in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const verifyToken = urlParams.get('token')
    if (verifyToken) {
      // Verify the token automatically
      fetch(`${API_BASE_URL}/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: verifyToken }),
      })
        .then(async (res) => {
          const data = await res.json()
          if (res.ok) {
            setVerificationMessage('Email verified successfully! You can now sign in.')
            setShowVerification(false)
            setAuthMode('login')
            setShowAuthDrawer(true)
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname)
          } else {
            setVerificationMessage(data.detail || 'Verification failed')
            setShowVerification(true)
          }
        })
        .catch(() => {
          setVerificationMessage('Verification failed. Please try again.')
          setShowVerification(true)
        })
    }
  }, [])

  async function handleJoinWaitlist(e) {
    e.preventDefault()
    if (!email) {
      setMessage('Please enter a valid email.')
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      const data = await response.json()
      setMessage(data.message || 'You are on the list!')
      setEmail('')
    } catch (error) {
      setMessage('Could not reach backend. Ensure the API server is running.')
    }
  }

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/deals?q=${encodeURIComponent(query)}`)
      const data = await response.json()
      setDeals(data.results || [])
    } catch (error) {
      setDeals([])
    } finally {
      setLoading(false)
    }
  }

  async function handleAuthSubmit(e) {
    e.preventDefault()
    if (!authEmail || !authPassword) {
      setMessage('Email and password are required.')
      return
    }

    setAuthLoading(true)
    setMessage('')

    try {
      const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register'
      const payload = authMode === 'login'
        ? { email: authEmail, password: authPassword }
        : { email: authEmail, password: authPassword, name: authName || authEmail.split('@')[0] }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const contentType = response.headers.get('content-type') || ''
      if (!contentType.includes('application/json')) {
        const rawText = await response.text()
        throw new Error(rawText.slice(0, 180) || 'Authentication endpoint returned a non-JSON response.')
      }

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed')
      }

      if (authMode === 'login') {
        const token = data.session?.token
        const user = data.session?.user
        
        if (!user) {
          throw new Error('Invalid response from server')
        }
        
        // Check if email is verified
        if (!user.emailVerified) {
          setVerificationEmail(authEmail)
          setShowVerification(true)
          setShowAuthDrawer(false)
          return
        }
        
        if (token) {
          localStorage.setItem(AUTH_TOKEN_KEY, token)
        }
        setAuthUser(user)
        setMessage('Login successful!')
      } else {
        setMessage(data.message || 'Account created successfully. Please check your email to verify your account.')
        setShowAuthDrawer(false)
      }

      setAuthEmail('')
      setAuthPassword('')
      setAuthName('')
    } catch (error) {
      setMessage(error.message || 'Authentication failed.')
    } finally {
      setAuthLoading(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    setAuthUser(null)
    setMessage('You have been logged out.')
  }

  async function handleResendVerification(e) {
    e.preventDefault()
    if (!verificationEmail) return
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: verificationEmail }),
      })
      const data = await response.json()
      setVerificationMessage(data.message || 'Verification email sent')
    } catch (error) {
      setVerificationMessage('Failed to resend verification email')
    }
  }

  async function handleVerifyToken(e) {
    e.preventDefault()
    const token = new URLSearchParams(window.location.search).get('token')
    if (!token) {
      setVerificationMessage('No verification token found')
      return
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })
      const data = await response.json()
      if (response.ok) {
        setVerificationMessage('Email verified successfully! You can now sign in.')
        setShowVerification(false)
        setAuthMode('login')
        setShowAuthDrawer(true)
      } else {
        setVerificationMessage(data.detail || 'Verification failed')
      }
    } catch (error) {
      setVerificationMessage('Verification failed. Please try again.')
    }
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand">💰 SmartDailySavings</div>
        <nav className="nav-center">
          <a href="#deals">Deals</a>
          <a href="#categories">Categories</a>
        </nav>
        <div className="nav-right">
          {!authUser && (
            <>
              <button className="nav-button secondary" onClick={() => {
                setAuthMode('login')
                setShowAuthDrawer(true)
              }}>Login</button>
              <button className="nav-button" onClick={() => {
                setAuthMode('register')
                setShowAuthDrawer(true)
              }}>Register</button>
            </>
          )}
          {authUser && (
            <div className="user-menu">
              <button className="nav-button" onClick={() => setShowProfile(!showProfile)}>
                {authUser.name || authUser.email}
              </button>
              {showProfile && (
                <div className="profile-dropdown">
                  <h4>Profile</h4>
                  <p><strong>Name:</strong> {authUser.name || '—'}</p>
                  <p><strong>Email:</strong> {authUser.email}</p>
                  <p><strong>Role:</strong> {authUser.role || 'user'}</p>
                  <p><strong>Email Verified:</strong> {authUser.emailVerified ? 'Yes' : 'No'}</p>
                  {authUser.sessionExpiresAt && (
                    <p><strong>Session expires:</strong> {new Date(authUser.sessionExpiresAt).toLocaleString()}</p>
                  )}
                  <button className="nav-button" onClick={handleLogout} style={{ marginTop: '10px', width: '100%' }}>Logout</button>
                </div>
              )}
            </div>
          )}
          <a href="#waitlist" className="cta">Get Early Access</a>
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">India's AI-powered savings app</p>
          <h1>Compare the best deals before you buy.</h1>
          <p className="subtext">Track price drops across Amazon, Flipkart, Blinkit, 1mg and more.</p>

          <form className="searchbar" onSubmit={handleSearch}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search groceries, medicine, gadgets..."
            />
            <button type="submit" disabled={loading}>{loading ? 'Searching...' : 'Search'}</button>
          </form>

          <form id="waitlist" className="waitlist-form" onSubmit={handleJoinWaitlist}>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email for early access"
            />
            <button type="submit">Notify Me</button>
          </form>

          {message && <p className="message">{message}</p>}
        </div>

        <div className="hero-card">
          <div className="small-tag">AI Verified</div>
          <h3>Today’s savings</h3>
          <div className="stats">
            <div><strong>25+</strong><span>platforms</span></div>
            <div><strong>₹8K</strong><span>avg. savings</span></div>
            <div><strong>14</strong><span>fake discounts flagged</span></div>
          </div>
        </div>
      </section>

      <main id="deals" className="content">
        <div className="section-heading">
          <h2>🔥 Top Deals Today</h2>
          <a href="#">View all</a>
        </div>

        <div className="category-pills">
          {categories.map((cat) => (
            <button
              key={cat}
              className={category === cat ? 'pill-active' : 'pill'}
              onClick={() => setCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="deal-grid">
          {deals.length === 0 ? (
            <div className="empty-state">No deals found.</div>
          ) : (
            deals
              .filter((deal) => category === 'All' || deal.category === category)
              .map((deal, index) => (
                <article key={`${deal.platform}-${index}`} className="deal-card">
                  {deal.isNew && <span className="new-badge">New</span>}
                  <div className="deal-emoji">📦</div>
                  <div className="deal-platform">{deal.platform}</div>
                  <h3>{deal.title}</h3>
                  <div className="deal-pricing">
                    <span className="price">{deal.price}</span>
                    <span className="mrp">{deal.mrp}</span>
                  </div>
                  <div className="deal-footer">
                    <span className="discount">{deal.discount}</span>
                    <span className="votes">👍 {deal.votes}</span>
                  </div>
                </article>
              ))
          )}
        </div>
      </main>

      {showAuthDrawer && !authUser && (
        <div className="auth-drawer-overlay" onClick={() => setShowAuthDrawer(false)} />
      )}
      {showAuthDrawer && !authUser && (
        <aside className="auth-drawer" role="dialog" aria-modal="true" aria-labelledby="auth-drawer-title">
          <div className="auth-drawer-header">
            <h2 id="auth-drawer-title">Welcome Back</h2>
            <p>Sign in or register</p>
            <button className="auth-drawer-close" onClick={() => setShowAuthDrawer(false)} aria-label="Close">
              ×
            </button>
          </div>
          <div className="auth-drawer-body">
            {showVerification ? (
              <div className="auth-verification">
                <div className="auth-verification-icon">📧</div>
                <h3>Verify Your Email</h3>
                <p>We've sent a verification link to <strong>{verificationEmail}</strong></p>
                <p className="auth-verification-sub">Click the link in the email to verify your account, then return here to sign in.</p>
                
                {verificationMessage && <p className={`auth-message ${verificationMessage.includes('success') ? 'success' : 'error'}`}>{verificationMessage}</p>}
                
                <div className="auth-verification-actions">
                  <button className="auth-social-btn" onClick={handleResendVerification}>
                    Resend Verification Email
                  </button>
                  <button className="auth-social-btn" onClick={() => {
                    setShowVerification(false)
                    setAuthMode('login')
                  }}>
                    Back to Sign In
                  </button>
                </div>
                
                <div className="auth-divider">
                  <span>or</span>
                </div>
                
                <form className="auth-form" onSubmit={handleVerifyToken}>
                  <p className="auth-verification-manual">Have a verification link? Enter the token manually:</p>
                  <input
                    type="text"
                    placeholder="Verification token"
                    onChange={(e) => setVerificationMessage('')}
                  />
                  <button type="submit">Verify</button>
                </form>
              </div>
            ) : (
              <>
                <div className="auth-social">
                  <button type="button" className="auth-social-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/></svg>
                    <span>Continue with Google</span>
                  </button>
                  <button type="button" className="auth-social-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M17.05 16.06c-.98 0-1.72-.8-1.72-1.79 0-.75.37-1.32 1.17-1.72V7H14V5h4v12h-3.95v-2.94zM8 5H6.13l-.03 12H8V11.77c0-2.05 2.26-3.2 3.83-3.2 2.52 0 3.15 1.52 3.15 3.2V17H20v3h-4v4h-4v-4H8V5zm8.58 8.64c-.75 0-1.32-.5-1.32-1.25 0-.6.42-1.25 1.18-1.25.7 0 1.33.46 1.33 1.14 0 .8-.53 1.36-1.19 1.36z"/></svg>
                    <span>Continue with Apple</span>
                  </button>
                </div>
                <div className="auth-divider">
                  <span>or</span>
                </div>
                <div className="auth-tabs">
                  <button
                    type="button"
                    className={authMode === 'login' ? 'auth-tab active' : 'auth-tab'}
                    onClick={() => setAuthMode('login')}
                  >
                    Login
                  </button>
                  <button
                    type="button"
                    className={authMode === 'register' ? 'auth-tab active' : 'auth-tab'}
                    onClick={() => setAuthMode('register')}
                  >
                    Register
                  </button>
                </div>
                <form className="auth-form" onSubmit={handleAuthSubmit}>
                  {authMode === 'register' && (
                    <input
                      type="text"
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      placeholder="Your name"
                    />
                  )}
                  <input
                    type="email"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="Email"
                  />
                  <input
                    type="password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="Password"
                  />
                  <button type="submit" disabled={authLoading}>
                    {authLoading ? 'Please wait...' : authMode === 'login' ? 'Continue' : 'Create Account'}
                  </button>
                </form>
                <div className="auth-footer">
                  {authMode === 'login' && (
                    <p>New customer? <button type="button" onClick={() => setAuthMode('register')}>Create an account</button></p>
                  )}
                  <p className="auth-guest"><button type="button" onClick={() => setShowAuthDrawer(false)}>Checkout as Guest</button></p>
                </div>
              </>
            )}
          </div>
        </aside>
      )}
    </div>
  )
}

export default App
