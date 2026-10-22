import { useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const defaultDeals = [
  { platform: 'BigBasket', title: 'Fortune Sunlite Refined Sunflower Oil 5L', price: '₹549', mrp: '₹620', discount: '54% OFF', votes: 143 },
  { platform: '1mg', title: 'Metformin 500mg Generic — 60 tablets', price: '₹38', mrp: '₹245', discount: 'GENERIC', votes: 89 },
  { platform: 'Flipkart', title: 'boAt Airdopes 141 True Wireless Earbuds', price: '₹899', mrp: '₹1,499', discount: '40% OFF', votes: 312 },
  { platform: 'Meesho', title: 'Cotton Solid Baseball Cap — Unisex', price: '₹129', mrp: '₹399', discount: '67% OFF', votes: 204 },
]

function App() {
  const [email, setEmail] = useState('')
  const [query, setQuery] = useState('iphone')
  const [deals, setDeals] = useState(defaultDeals)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

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

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand">💰 SmartDailySavings</div>
        <nav className="nav">
          <a href="#deals">Deals</a>
          <a href="#categories">Categories</a>
          <a href="#waitlist" className="cta">Get Early Access</a>
        </nav>
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

        <div className="deal-grid">
          {deals.length === 0 ? (
            <div className="empty-state">No deals found.</div>
          ) : (
            deals.map((deal, index) => (
              <article key={`${deal.platform}-${index}`} className="deal-card">
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
