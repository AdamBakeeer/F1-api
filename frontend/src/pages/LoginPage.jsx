import { useState } from 'react'
import './Auth.css'

function LoginPage({ onLoginSuccess, goToSignup, goHome }) {
  const [mode, setMode] = useState('user') // user | admin
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      setLoading(true)
      setError('')

      const endpoint =
        mode === 'admin'
          ? 'http://127.0.0.1:8000/auth/admin/login'
          : 'http://127.0.0.1:8000/auth/login'

      const payload =
        mode === 'admin'
          ? {
              email: formData.email,
              password: formData.password
            }
          : {
              email: formData.email,
              password: formData.password
            }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      if (mode === 'admin') {
        onLoginSuccess({
          token: data.access_token,
          user: {
            username: 'admin',
            email: 'admin',
            role: 'admin'
          }
        })
      } else {
        onLoginSuccess({
          token: data.access_token,
          user: {
            ...data.user,
            role: 'user'
          }
        })
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-top-line"></div>

        <h2>Login</h2>
        <p className="auth-subtitle">
          Access your F1 Data Platform account.
        </p>

        <div className="auth-mode-toggle">
          <button
            className={mode === 'user' ? 'auth-mode-btn active-auth-mode' : 'auth-mode-btn'}
            onClick={() => setMode('user')}
            type="button"
          >
            User
          </button>
          <button
            className={mode === 'admin' ? 'auth-mode-btn active-auth-mode' : 'auth-mode-btn'}
            onClick={() => setMode('admin')}
            type="button"
          >
            Admin
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="text"
            name="email"
            placeholder={mode === 'admin' ? 'Admin username' : 'Email'}
            value={formData.email}
            onChange={handleChange}
            className="auth-input"
            required
          />

          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            className="auth-input"
            required
          />

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-footer">
          <button onClick={goToSignup} className="auth-link-btn" type="button">
            Create account
          </button>
          <button onClick={goHome} className="auth-link-btn" type="button">
            Back home
          </button>
        </div>
      </div>
    </div>
  )
}

export default LoginPage