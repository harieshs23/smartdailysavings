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
        if (token) {
          localStorage.setItem(AUTH_TOKEN_KEY, token)
        }
        setAuthUser(data.session?.user || null)
        setMessage('Login successful!')
      } else {
        setMessage('Account created successfully. Please sign in.')
        setAuthMode('login')
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

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand">💰 SmartDailySavings</div>
        <nav className="nav-center">
          <a href="#deals">Deals</a>
          <a href="#categories">Categories</a>
        </nav>
        <div className="nav-right">
          {authUser ? (
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
          ) : null}
        </div>
      </header>

      <section className="hero">
        <div className="auth-top">
          {authUser ? null : (
            <>
              <button className="nav-button secondary" onClick={() => setAuthMode('login')}>Login</button>
              {authMode === 'login' && (
                <select
                  className="nav-button secondary"
                  style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                  onChange={(e) => setRegion(e.target.value)}
                >
                  <option value="">Select region</option>
                  <option value="india">India</option>
                  <option value="us">United States</option>
                  <option value="uk">United Kingdom</option>
                  <option value="ca">Canada</option>
                </select>
              )}
              <button className="nav-button" onClick={() => setAuthMode('register')}>Register</button>
            </>
          )}
        </div>
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

          <div className="auth-card">
                      {!authUser && (
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
                      )}

                      <form className="auth-form" onSubmit={handleAuthSubmit}>
                        {!authUser && authMode === 'register' && (
                          <input
                            type="text"
                            value={authName}
                            onChange={(e) => setAuthName(e.target.value)}
                            placeholder="Your name"
                          />
                        )}
                        {!authUser && (
                          <input
                            type="email"
                            value={authEmail}
                            onChange={(e) => setAuthEmail(e.target.value)}
                            placeholder="Email"
                          />
                        )}
                        {!authUser && (
                          <input
                            type="password"
                            value={authPassword}
                            onChange={(e) => setAuthPassword(e.target.value)}
                            placeholder="Password"
                          />
                        )}
                        {!authUser && (
                          <button type="submit" disabled={authLoading}>
                            {authLoading ? 'Please wait...' : authMode === 'login' ? 'Sign In' : 'Create Account'}
                          </button>
                        )}
                        {authUser && <p style={{ color: '#a7f3d0', textAlign: 'center' }}>Signed in as {authUser.name || authUser.email}</p>}
                      </form>
                    </div>

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
    </div>
  )
}

export default App
