import { useEffect, useState } from 'react'
import { API_BASE_URL } from '../config.js'
import './CircuitDetailsPage.css'

function CircuitDetailsPage({ circuitSlug, goBack, token, currentUser }) {
  const [circuit, setCircuit] = useState(null)
  const [stats, setStats] = useState(null)
  const [races, setRaces] = useState([])
  const [winners, setWinners] = useState([])
  const [topDrivers, setTopDrivers] = useState([])
  const [topConstructors, setTopConstructors] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  const [isFavorite, setIsFavorite] = useState(false)
  const [favoriteLoading, setFavoriteLoading] = useState(false)
  const [favoriteMessage, setFavoriteMessage] = useState('')
  const [favoriteError, setFavoriteError] = useState('')

  useEffect(() => {
    fetchCircuitData()
  }, [circuitSlug])

  useEffect(() => {
    if (token && currentUser?.role === 'user' && circuitSlug) {
      checkFavoriteStatus()
    } else {
      setIsFavorite(false)
      setFavoriteMessage('')
      setFavoriteError('')
    }
  }, [token, currentUser, circuitSlug])

  const fetchCircuitData = async () => {
    try {
      setLoading(true)
      setError('')

      const [
        circuitRes,
        statsRes,
        racesRes,
        winnersRes,
        topDriversRes,
        topConstructorsRes
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/circuits/${circuitSlug}`),
        fetch(`${API_BASE_URL}/circuits/${circuitSlug}/stats`),
        fetch(`${API_BASE_URL}/circuits/${circuitSlug}/races`),
        fetch(`${API_BASE_URL}/circuits/${circuitSlug}/winners`),
        fetch(`${API_BASE_URL}/circuits/${circuitSlug}/top-drivers?limit=8`),
        fetch(`${API_BASE_URL}/circuits/${circuitSlug}/top-constructors?limit=8`)
      ])

      const circuitData = await circuitRes.json()
      const statsData = await statsRes.json()
      const racesData = await racesRes.json()
      const winnersData = await winnersRes.json()
      const topDriversData = await topDriversRes.json()
      const topConstructorsData = await topConstructorsRes.json()

      if (!circuitRes.ok) throw new Error(circuitData.detail || 'Failed to load circuit')
      if (!statsRes.ok) throw new Error(statsData.detail || 'Failed to load stats')
      if (!racesRes.ok) throw new Error(racesData.detail || 'Failed to load races')
      if (!winnersRes.ok) throw new Error(winnersData.detail || 'Failed to load winners')
      if (!topDriversRes.ok) throw new Error(topDriversData.detail || 'Failed to load top drivers')
      if (!topConstructorsRes.ok) throw new Error(topConstructorsData.detail || 'Failed to load top constructors')

      setCircuit(circuitData)
      setStats(statsData)
      setRaces(racesData.data || [])
      setWinners(winnersData.data || [])
      setTopDrivers(topDriversData.data || [])
      setTopConstructors(topConstructorsData.data || [])
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const checkFavoriteStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/favorites/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()
      if (!response.ok) return

      const favoriteCircuits = data.circuits || []
      setIsFavorite(favoriteCircuits.some((item) => item.circuit_slug === circuitSlug))
    } catch {
      setIsFavorite(false)
    }
  }

  const handleFavoriteToggle = async () => {
    try {
      setFavoriteLoading(true)
      setFavoriteError('')
      setFavoriteMessage('')

      const response = await fetch(`${API_BASE_URL}/favorites/circuits/${circuitSlug}`, {
        method: isFavorite ? 'DELETE' : 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update favorite')
      }

      setIsFavorite((prev) => !prev)
      setFavoriteMessage(isFavorite ? 'Removed from favorites' : 'Added to favorites')
    } catch (err) {
      setFavoriteError(err.message || 'Something went wrong')
    } finally {
      setFavoriteLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="circuit-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Circuits</button>
        <p className="circuit-details-message">Loading circuit details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="circuit-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Circuits</button>
        <p className="circuit-details-message error">{error}</p>
      </div>
    )
  }

  return (
    <div className="circuit-details-page">
      <button className="back-btn" onClick={goBack}>← Back to Circuits</button>

      {circuit && (
        <div className="circuit-profile-card">
          <div className="circuit-profile-top-line"></div>
          <h2>{circuit.name}</h2>
          <p><strong>Location:</strong> {circuit.location || 'N/A'}</p>
          <p><strong>Country:</strong> {circuit.country || 'N/A'}</p>
          <p><strong>Latitude:</strong> {circuit.lat ?? 'N/A'}</p>
          <p><strong>Longitude:</strong> {circuit.lng ?? 'N/A'}</p>
          <p><strong>Altitude:</strong> {circuit.alt ?? 'N/A'}</p>

          {currentUser?.role === 'user' && token && (
            <div className="favorite-action-box">
              <button
                className={isFavorite ? 'favorite-btn active-favorite-btn' : 'favorite-btn'}
                onClick={handleFavoriteToggle}
                disabled={favoriteLoading}
                type="button"
              >
                {favoriteLoading
                  ? 'Updating...'
                  : isFavorite
                    ? '♥ Remove from Favorites'
                    : '♡ Add to Favorites'}
              </button>

              {favoriteMessage && <p className="favorite-message success">{favoriteMessage}</p>}
              {favoriteError && <p className="favorite-message error">{favoriteError}</p>}
            </div>
          )}
        </div>
      )}

      <div className="details-tabs">
        <button
          className={activeTab === 'overview' ? 'details-tab active-details-tab' : 'details-tab'}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'races' ? 'details-tab active-details-tab' : 'details-tab'}
          onClick={() => setActiveTab('races')}
        >
          Hosted Races
        </button>
        <button
          className={activeTab === 'winners' ? 'details-tab active-details-tab' : 'details-tab'}
          onClick={() => setActiveTab('winners')}
        >
          Winners
        </button>
        <button
          className={activeTab === 'drivers' ? 'details-tab active-details-tab' : 'details-tab'}
          onClick={() => setActiveTab('drivers')}
        >
          Top Drivers
        </button>
        <button
          className={activeTab === 'constructors' ? 'details-tab active-details-tab' : 'details-tab'}
          onClick={() => setActiveTab('constructors')}
        >
          Top Constructors
        </button>
      </div>

      {activeTab === 'overview' && stats && (
        <div className="circuit-stats-section">
          <h3>Venue Intelligence</h3>
          <div className="circuit-stats-grid">
            <div className="circuit-stat-box"><span>Races Hosted</span><strong>{stats.races_hosted}</strong></div>
            <div className="circuit-stat-box"><span>First Season</span><strong>{stats.first_season}</strong></div>
            <div className="circuit-stat-box"><span>Last Season</span><strong>{stats.last_season}</strong></div>
            <div className="circuit-stat-box"><span>Unique Drivers</span><strong>{stats.unique_drivers}</strong></div>
            <div className="circuit-stat-box"><span>Unique Constructors</span><strong>{stats.unique_constructors}</strong></div>
            <div className="circuit-stat-box">
              <span>Avg Points / Result</span>
              <strong>{Number(stats.avg_points_awarded_per_result).toFixed(2)}</strong>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'races' && (
        <div className="circuit-table-section">
          <h3>Hosted Races</h3>
          <div className="circuit-table-wrapper">
            <table className="circuit-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Round</th>
                  <th>Race</th>
                  <th>Date</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {races.map((race) => (
                  <tr key={race.race_id}>
                    <td>{race.year}</td>
                    <td>{race.round}</td>
                    <td>{race.name}</td>
                    <td>{race.date}</td>
                    <td>{race.time || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'winners' && (
        <div className="circuit-table-section">
          <h3>Winners Through History</h3>
          <div className="circuit-table-wrapper">
            <table className="circuit-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Round</th>
                  <th>Race</th>
                  <th>Winner</th>
                  <th>Code</th>
                  <th>Constructor</th>
                </tr>
              </thead>
              <tbody>
                {winners.map((item, index) => (
                  <tr key={index}>
                    <td>{item.year}</td>
                    <td>{item.round}</td>
                    <td>{item.race_name}</td>
                    <td>{item.forename} {item.surname}</td>
                    <td>{item.code || 'N/A'}</td>
                    <td>{item.constructor_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'drivers' && (
        <div className="circuit-table-section">
          <h3>Top Drivers at this Circuit</h3>
          <div className="circuit-table-wrapper">
            <table className="circuit-table">
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Code</th>
                  <th>Nationality</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                  <th>Points</th>
                  <th>Entries</th>
                </tr>
              </thead>
              <tbody>
                {topDrivers.map((driver, index) => (
                  <tr key={index}>
                    <td>{driver.forename} {driver.surname}</td>
                    <td>{driver.code || 'N/A'}</td>
                    <td>{driver.nationality || 'N/A'}</td>
                    <td>{driver.wins}</td>
                    <td>{driver.podiums}</td>
                    <td>{driver.total_points}</td>
                    <td>{driver.race_entries}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'constructors' && (
        <div className="circuit-table-section">
          <h3>Top Constructors at this Circuit</h3>
          <div className="circuit-table-wrapper">
            <table className="circuit-table">
              <thead>
                <tr>
                  <th>Constructor</th>
                  <th>Nationality</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                  <th>Points</th>
                  <th>Entries</th>
                </tr>
              </thead>
              <tbody>
                {topConstructors.map((constructor, index) => (
                  <tr key={index}>
                    <td>{constructor.constructor_name}</td>
                    <td>{constructor.nationality || 'N/A'}</td>
                    <td>{constructor.wins}</td>
                    <td>{constructor.podiums}</td>
                    <td>{constructor.total_points}</td>
                    <td>{constructor.race_entries}</td>
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

export default CircuitDetailsPage