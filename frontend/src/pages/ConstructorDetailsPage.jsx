import { useEffect, useMemo, useState } from 'react'
import './ConstructorDetailsPage.css'

function ConstructorDetailsPage({ constructorSlug, goBack, token, currentUser }) {
  const [constructorData, setConstructorData] = useState(null)
  const [stats, setStats] = useState(null)
  const [drivers, setDrivers] = useState([])
  const [seasons, setSeasons] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedSeason, setSelectedSeason] = useState('')

  const [isFavorite, setIsFavorite] = useState(false)
  const [favoriteLoading, setFavoriteLoading] = useState(false)
  const [favoriteMessage, setFavoriteMessage] = useState('')
  const [favoriteError, setFavoriteError] = useState('')

  useEffect(() => {
    fetchConstructorData()
  }, [constructorSlug])

  useEffect(() => {
    if (token && currentUser?.role === 'user' && constructorSlug) {
      checkFavoriteStatus()
    } else {
      setIsFavorite(false)
    }
  }, [token, currentUser, constructorSlug])

  const fetchConstructorData = async () => {
    try {
      setLoading(true)
      setError('')

      const [constructorRes, statsRes, driversRes, seasonsRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/stats`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/drivers`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/seasons`)
      ])

      const constructorJson = await constructorRes.json()
      const statsJson = await statsRes.json()
      const driversJson = await driversRes.json()
      const seasonsJson = await seasonsRes.json()

      if (!constructorRes.ok) throw new Error(constructorJson.detail || 'Failed to load constructor')
      if (!statsRes.ok) throw new Error(statsJson.detail || 'Failed to load stats')
      if (!driversRes.ok) throw new Error(driversJson.detail || 'Failed to load drivers')
      if (!seasonsRes.ok) throw new Error(seasonsJson.detail || 'Failed to load seasons')

      setConstructorData(constructorJson)
      setStats(statsJson.data)
      setDrivers(driversJson.data || [])
      setSeasons(seasonsJson.data || [])

      if ((seasonsJson.data || []).length > 0) {
        const latestYear = String(seasonsJson.data[seasonsJson.data.length - 1].year)
        setSelectedSeason(latestYear)
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const checkFavoriteStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/favorites/', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()
      if (!response.ok) return

      const favoriteConstructors = data.constructors || []
      setIsFavorite(favoriteConstructors.some((item) => item.constructor_slug === constructorSlug))
    } catch {
      setIsFavorite(false)
    }
  }

  const handleFavoriteToggle = async () => {
    try {
      setFavoriteLoading(true)
      setFavoriteError('')
      setFavoriteMessage('')

      const method = isFavorite ? 'DELETE' : 'POST'

      const response = await fetch(`http://127.0.0.1:8000/favorites/constructors/${constructorSlug}`, {
        method,
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update favorite')
      }

      setIsFavorite(!isFavorite)
      setFavoriteMessage(isFavorite ? 'Removed from favorites' : 'Added to favorites')
    } catch (err) {
      setFavoriteError(err.message || 'Something went wrong')
    } finally {
      setFavoriteLoading(false)
    }
  }

  const filteredDrivers = useMemo(() => {
    if (!selectedSeason) return drivers
    return drivers.filter((driver) =>
      String(driver.first_season) <= selectedSeason && String(driver.last_season) >= selectedSeason
    )
  }, [drivers, selectedSeason])

  const seasonOptions = useMemo(() => seasons.map((item) => String(item.year)), [seasons])

  if (loading) {
    return (
      <div className="constructor-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Constructors</button>
        <p className="constructor-details-message">Loading constructor details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="constructor-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Constructors</button>
        <p className="constructor-details-message error">{error}</p>
      </div>
    )
  }

  return (
    <div className="constructor-details-page">
      <button className="back-btn" onClick={goBack}>← Back to Constructors</button>

      {constructorData && (
        <div className="constructor-profile-card">
          <div className="constructor-profile-top-line"></div>
          <h2>{constructorData.name}</h2>
          <p><strong>Nationality:</strong> {constructorData.nationality || 'N/A'}</p>
          <p><strong>Slug:</strong> {constructorData.constructor_slug}</p>

          {currentUser?.role === 'user' && token && (
            <div className="favorite-action-box">
              <button
                className={isFavorite ? 'favorite-btn active-favorite-btn' : 'favorite-btn'}
                onClick={handleFavoriteToggle}
                disabled={favoriteLoading}
                type="button"
              >
                {favoriteLoading ? 'Updating...' : isFavorite ? '♥ Remove from Favorites' : '♡ Add to Favorites'}
              </button>

              {favoriteMessage && <p className="favorite-message success">{favoriteMessage}</p>}
              {favoriteError && <p className="favorite-message error">{favoriteError}</p>}
            </div>
          )}
        </div>
      )}

      <div className="details-tabs">
        <button className={activeTab === 'overview' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={activeTab === 'drivers' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('drivers')}>
          Drivers
        </button>
        <button className={activeTab === 'seasons' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('seasons')}>
          Seasons
        </button>
      </div>

      {activeTab === 'overview' && stats && (
        <div className="constructor-stats-section">
          <h3>Constructor Statistics</h3>
          <div className="stats-grid">
            <div className="stat-box"><span>Race Entries</span><strong>{stats.race_entries}</strong></div>
            <div className="stat-box"><span>Total Points</span><strong>{stats.total_points}</strong></div>
            <div className="stat-box"><span>Wins</span><strong>{stats.wins}</strong></div>
            <div className="stat-box"><span>Podiums</span><strong>{stats.podiums}</strong></div>
            <div className="stat-box"><span>First Season</span><strong>{stats.first_season}</strong></div>
            <div className="stat-box"><span>Last Season</span><strong>{stats.last_season}</strong></div>
          </div>
        </div>
      )}

      {activeTab === 'drivers' && (
        <div className="constructor-results-section">
          <h3>Drivers</h3>

          <div className="details-filters">
            <select
              value={selectedSeason}
              onChange={(e) => setSelectedSeason(e.target.value)}
              className="details-select"
            >
              <option value="">All Seasons</option>
              {seasonOptions.map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div className="results-table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Code</th>
                  <th>Nationality</th>
                  <th>First Season</th>
                  <th>Last Season</th>
                  <th>Entries</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {filteredDrivers.map((driver, index) => (
                  <tr key={index}>
                    <td>{driver.forename} {driver.surname}</td>
                    <td>{driver.code || 'N/A'}</td>
                    <td>{driver.nationality || 'N/A'}</td>
                    <td>{driver.first_season}</td>
                    <td>{driver.last_season}</td>
                    <td>{driver.race_entries}</td>
                    <td>{driver.wins}</td>
                    <td>{driver.podiums}</td>
                    <td>{driver.total_points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'seasons' && (
        <div className="constructor-results-section">
          <h3>Season History</h3>
          <div className="results-table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Season</th>
                  <th>Entries</th>
                  <th>Points</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                </tr>
              </thead>
              <tbody>
                {seasons.map((season, index) => (
                  <tr key={index}>
                    <td>{season.year}</td>
                    <td>{season.race_entries}</td>
                    <td>{season.total_points}</td>
                    <td>{season.wins}</td>
                    <td>{season.podiums}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default ConstructorDetailsPage