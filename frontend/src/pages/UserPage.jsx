import { useEffect, useState } from 'react'
import { API_BASE_URL } from '../config.js'
import './UserPage.css'

function UserPage({ currentUser, token, onUserUpdate, onLogout, goHome }) {
  const [formData, setFormData] = useState({
    username: currentUser?.username || '',
    email: currentUser?.email || '',
    password: ''
  })

  const [favorites, setFavorites] = useState({
    drivers: [],
    constructors: [],
    circuits: []
  })

  const [loading, setLoading] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [favoritesLoading, setFavoritesLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [favoritesError, setFavoritesError] = useState('')

  useEffect(() => {
    if (token && currentUser?.role === 'user') {
      fetchFavorites()
    }
  }, [token, currentUser])

  const fetchFavorites = async () => {
    try {
      setFavoritesLoading(true)
      setFavoritesError('')

      const response = await fetch(`${API_BASE_URL}/favorites/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to load favorites')
      }

      setFavorites({
        drivers: data.drivers || [],
        constructors: data.constructors || [],
        circuits: data.circuits || []
      })
    } catch (err) {
      setFavoritesError(err.message || 'Something went wrong')
    } finally {
      setFavoritesLoading(false)
    }
  }

  const handleRemoveFavorite = async (type, slug) => {
    try {
      setFavoritesError('')

      const response = await fetch(`${API_BASE_URL}/favorites/${type}/${slug}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to remove favorite')
      }

      await fetchFavorites()
    } catch (err) {
      setFavoritesError(err.message || 'Something went wrong')
    }
  }

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleUpdate = async (e) => {
    e.preventDefault()

    try {
      setLoading(true)
      setError('')
      setMessage('')

      const payload = {}
      if (formData.username.trim()) payload.username = formData.username.trim()
      if (formData.email.trim()) payload.email = formData.email.trim()
      if (formData.password.trim()) payload.password = formData.password.trim()

      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update account')
      }

      onUserUpdate({
        ...currentUser,
        ...data
      })

      setFormData((prev) => ({
        ...prev,
        password: ''
      }))

      setMessage('Account updated successfully')
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    const confirmed = window.confirm('Are you sure you want to delete your account? This cannot be undone.')
    if (!confirmed) return

    try {
      setDeleteLoading(true)
      setError('')
      setMessage('')

      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to delete account')
      }

      onLogout()
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setDeleteLoading(false)
    }
  }

  if (!currentUser) {
    return (
      <div className="user-page">
        <p className="user-message error">No user is logged in.</p>
      </div>
    )
  }

  return (
    <div className="user-page">
      <div className="user-profile-card">
        <div className="user-top-line"></div>
        <h2>My Account</h2>
        <p><strong>Username:</strong> {currentUser.username}</p>
        <p><strong>Email:</strong> {currentUser.email}</p>
        <p><strong>Role:</strong> {currentUser.role}</p>
      </div>

      <div className="user-edit-card">
        <h3>Update Account</h3>

        <form onSubmit={handleUpdate} className="user-form">
          <input
            type="text"
            name="username"
            placeholder="New username"
            value={formData.username}
            onChange={handleChange}
            className="user-input"
          />

          <input
            type="email"
            name="email"
            placeholder="New email"
            value={formData.email}
            onChange={handleChange}
            className="user-input"
          />

          <input
            type="password"
            name="password"
            placeholder="New password (optional)"
            value={formData.password}
            onChange={handleChange}
            className="user-input"
          />

          {message && <p className="user-message success">{message}</p>}
          {error && <p className="user-message error">{error}</p>}

          <button type="submit" className="user-save-btn" disabled={loading}>
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      <div className="user-favorites-card">
        <h3>My Favorites</h3>

        {favoritesError && <p className="user-message error">{favoritesError}</p>}
        {favoritesLoading && <p className="user-note">Loading favorites...</p>}

        {!favoritesLoading && (
          <div className="favorites-grid">
            <div className="favorite-section">
              <h4>Favorite Drivers</h4>
              {favorites.drivers.length === 0 ? (
                <p className="user-note">No favorite drivers yet.</p>
              ) : (
                <div className="favorite-list">
                  {favorites.drivers.map((driver) => (
                    <div key={driver.driver_id} className="favorite-item">
                      <div>
                        <p className="favorite-title">
                          {driver.forename} {driver.surname}
                        </p>
                        <p className="favorite-meta">
                          {driver.code || 'N/A'} • {driver.nationality || 'N/A'}
                        </p>
                      </div>
                      <button
                        type="button"
                        className="favorite-remove-btn"
                        onClick={() => handleRemoveFavorite('drivers', driver.driver_slug)}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="favorite-section">
              <h4>Favorite Constructors</h4>
              {favorites.constructors.length === 0 ? (
                <p className="user-note">No favorite constructors yet.</p>
              ) : (
                <div className="favorite-list">
                  {favorites.constructors.map((constructor) => (
                    <div key={constructor.constructor_id} className="favorite-item">
                      <div>
                        <p className="favorite-title">{constructor.name}</p>
                        <p className="favorite-meta">{constructor.nationality || 'N/A'}</p>
                      </div>
                      <button
                        type="button"
                        className="favorite-remove-btn"
                        onClick={() => handleRemoveFavorite('constructors', constructor.constructor_slug)}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="favorite-section">
              <h4>Favorite Circuits</h4>
              {favorites.circuits.length === 0 ? (
                <p className="user-note">No favorite circuits yet.</p>
              ) : (
                <div className="favorite-list">
                  {favorites.circuits.map((circuit) => (
                    <div key={circuit.circuit_id} className="favorite-item">
                      <div>
                        <p className="favorite-title">{circuit.name}</p>
                        <p className="favorite-meta">
                          {circuit.location || 'N/A'} • {circuit.country || 'N/A'}
                        </p>
                      </div>
                      <button
                        type="button"
                        className="favorite-remove-btn"
                        onClick={() => handleRemoveFavorite('circuits', circuit.circuit_slug)}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="user-danger-card">
        <h3>Danger Zone</h3>
        <button
          onClick={handleDelete}
          className="user-delete-btn"
          disabled={deleteLoading}
          type="button"
        >
          {deleteLoading ? 'Deleting...' : 'Delete Account'}
        </button>

        <div className="user-bottom-actions">
          <button onClick={onLogout} className="user-secondary-btn" type="button">
            Logout
          </button>
          <button onClick={goHome} className="user-secondary-btn" type="button">
            Back Home
          </button>
        </div>
      </div>
    </div>
  )
}

export default UserPage