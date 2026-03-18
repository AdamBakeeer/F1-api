import { useEffect, useMemo, useState } from 'react'
import { API_BASE_URL } from '../config.js'
import './DriverDetailsPage.css'

function DriverDetailsPage({ driverSlug, goBack, token, currentUser }) {
  const [driver, setDriver] = useState(null)
  const [stats, setStats] = useState(null)
  const [results, setResults] = useState([])
  const [seasons, setSeasons] = useState([])
  const [teams, setTeams] = useState([])
  const [teammates, setTeammates] = useState([])
  const [bestCircuits, setBestCircuits] = useState([])
  const [dnfs, setDnfs] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  const [selectedSeason, setSelectedSeason] = useState('')
  const [selectedTeam, setSelectedTeam] = useState('')

  const [isFavorite, setIsFavorite] = useState(false)
  const [favoriteLoading, setFavoriteLoading] = useState(false)
  const [favoriteMessage, setFavoriteMessage] = useState('')
  const [favoriteError, setFavoriteError] = useState('')

  useEffect(() => {
    fetchDriverCoreData()
  }, [driverSlug])

  useEffect(() => {
    if (driverSlug) {
      fetchTeammates()
    }
  }, [driverSlug, selectedSeason])

  useEffect(() => {
    if (token && currentUser?.role === 'user' && driverSlug) {
      checkFavoriteStatus()
    } else {
      setIsFavorite(false)
    }
  }, [token, currentUser, driverSlug])

  const fetchDriverCoreData = async () => {
    try {
      setLoading(true)
      setError('')

      const [
        driverRes,
        statsRes,
        resultsRes,
        seasonsRes,
        teamsRes,
        circuitsRes,
        dnfsRes
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/drivers/${driverSlug}`),
        fetch(`${API_BASE_URL}/drivers/${driverSlug}/stats`),
        fetch(`${API_BASE_URL}/drivers/${driverSlug}/results?limit=10`),
        fetch(`${API_BASE_URL}/drivers/${driverSlug}/seasons`),
        fetch(`${API_BASE_URL}/drivers/${driverSlug}/teams`),
        fetch(`${API_BASE_URL}/drivers/${driverSlug}/best-circuits?limit=5`),
        fetch(`${API_BASE_URL}/drivers/${driverSlug}/dnfs`)
      ])

      const driverData = await driverRes.json()
      const statsData = await statsRes.json()
      const resultsData = await resultsRes.json()
      const seasonsData = await seasonsRes.json()
      const teamsData = await teamsRes.json()
      const circuitsData = await circuitsRes.json()
      const dnfsData = await dnfsRes.json()

      if (!driverRes.ok) throw new Error(driverData.detail || 'Failed to load driver')
      if (!statsRes.ok) throw new Error(statsData.detail || 'Failed to load stats')
      if (!resultsRes.ok) throw new Error(resultsData.detail || 'Failed to load results')
      if (!seasonsRes.ok) throw new Error(seasonsData.detail || 'Failed to load seasons')
      if (!teamsRes.ok) throw new Error(teamsData.detail || 'Failed to load teams')
      if (!circuitsRes.ok) throw new Error(circuitsData.detail || 'Failed to load circuits')
      if (!dnfsRes.ok) throw new Error(dnfsData.detail || 'Failed to load DNF data')

      setDriver(driverData)
      setStats(statsData.data)
      setResults(resultsData.data || [])
      setSeasons(seasonsData.data || [])
      setTeams(teamsData.data || [])
      setBestCircuits(circuitsData.data || [])
      setDnfs(dnfsData)

      if ((seasonsData.data || []).length > 0) {
        const latestYear = String(seasonsData.data[seasonsData.data.length - 1].year)
        setSelectedSeason(latestYear)
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const fetchTeammates = async () => {
    try {
      let url = `${API_BASE_URL}/drivers/${driverSlug}/teammates`

      if (selectedSeason) {
        url += `?year=${selectedSeason}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to load teammates')
      }

      setTeammates(data.data || [])
    } catch {
      setTeammates([])
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

      const favoriteDrivers = data.drivers || []
      const exists = favoriteDrivers.some((item) => item.driver_slug === driverSlug)
      setIsFavorite(exists)
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

      const response = await fetch(`${API_BASE_URL}/favorites/drivers/${driverSlug}`, {
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

  const seasonOptions = useMemo(() => {
    return seasons.map((item) => String(item.year))
  }, [seasons])

  const filteredTeammates = useMemo(() => {
    if (!selectedTeam) return teammates
    return teammates.filter((mate) => mate.constructor_name === selectedTeam)
  }, [teammates, selectedTeam])

  const teammateTeams = useMemo(() => {
    const unique = [...new Set(teammates.map((item) => item.constructor_name).filter(Boolean))]
    return unique.sort()
  }, [teammates])

  if (loading) {
    return (
      <div className="driver-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Drivers</button>
        <p className="driver-details-message">Loading driver details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="driver-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Drivers</button>
        <p className="driver-details-message error">{error}</p>
      </div>
    )
  }

  return (
    <div className="driver-details-page">
      <button className="back-btn" onClick={goBack}>← Back to Drivers</button>

      {driver && (
        <div className="driver-profile-card">
          <div className="driver-profile-top-line"></div>
          <h2>{driver.forename} {driver.surname}</h2>
          <p><strong>Code:</strong> {driver.code || 'N/A'}</p>
          <p><strong>Nationality:</strong> {driver.nationality || 'N/A'}</p>
          <p><strong>Date of Birth:</strong> {driver.dob || 'N/A'}</p>
          <p><strong>Slug:</strong> {driver.driver_slug}</p>

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
        <button className={activeTab === 'overview' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={activeTab === 'results' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('results')}>
          Results
        </button>
        <button className={activeTab === 'teams' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('teams')}>
          Teams
        </button>
        <button className={activeTab === 'teammates' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('teammates')}>
          Teammates
        </button>
        <button className={activeTab === 'circuits' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('circuits')}>
          Best Circuits
        </button>
        <button className={activeTab === 'dnfs' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('dnfs')}>
          DNFs
        </button>
      </div>

      {activeTab === 'overview' && (
        <>
          {stats && (
            <div className="driver-stats-section">
              <h3>Career Statistics</h3>
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

          <div className="driver-seasons-section">
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
        </>
      )}

      {activeTab === 'results' && (
        <div className="driver-results-section">
          <h3>Recent Results</h3>
          <div className="results-table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Round</th>
                  <th>Race</th>
                  <th>Team</th>
                  <th>Finish</th>
                  <th>Points</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result, index) => (
                  <tr key={index}>
                    <td>{result.year}</td>
                    <td>{result.round}</td>
                    <td>{result.race_name}</td>
                    <td>{result.constructor_name}</td>
                    <td>{result.finish_position ?? 'N/A'}</td>
                    <td>{result.points}</td>
                    <td>{result.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'teams' && (
        <div className="driver-results-section">
          <h3>Teams</h3>
          <div className="results-table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Team</th>
                  <th>Nationality</th>
                  <th>First Season</th>
                  <th>Last Season</th>
                  <th>Entries</th>
                  <th>Wins</th>
                </tr>
              </thead>
              <tbody>
                {teams.map((team, index) => (
                  <tr key={index}>
                    <td>{team.constructor_name}</td>
                    <td>{team.nationality}</td>
                    <td>{team.first_season}</td>
                    <td>{team.last_season}</td>
                    <td>{team.race_entries}</td>
                    <td>{team.wins}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'teammates' && (
        <div className="driver-results-section">
          <h3>Teammates</h3>

          <div className="details-filters">
            <select
              value={selectedSeason}
              onChange={(e) => setSelectedSeason(e.target.value)}
              className="details-select"
            >
              <option value="">All Seasons</option>
              {seasonOptions.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>

            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="details-select"
            >
              <option value="">All Teams</option>
              {teammateTeams.map((team) => (
                <option key={team} value={team}>
                  {team}
                </option>
              ))}
            </select>
          </div>

          <div className="results-table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Teammate</th>
                  <th>Code</th>
                  <th>Team</th>
                  <th>First Overlap</th>
                  <th>Last Overlap</th>
                  <th>Shared Entries</th>
                </tr>
              </thead>
              <tbody>
                {filteredTeammates.map((mate, index) => (
                  <tr key={index}>
                    <td>{mate.teammate_forename} {mate.teammate_surname}</td>
                    <td>{mate.teammate_code || 'N/A'}</td>
                    <td>{mate.constructor_name}</td>
                    <td>{mate.first_overlap_season}</td>
                    <td>{mate.last_overlap_season}</td>
                    <td>{mate.shared_race_entries}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'circuits' && (
        <div className="driver-results-section">
          <h3>Best Circuits</h3>
          <div className="results-table-wrapper">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Circuit</th>
                  <th>Location</th>
                  <th>Country</th>
                  <th>Entries</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {bestCircuits.map((circuit, index) => (
                  <tr key={index}>
                    <td>{circuit.circuit_name}</td>
                    <td>{circuit.location}</td>
                    <td>{circuit.country}</td>
                    <td>{circuit.race_entries}</td>
                    <td>{circuit.wins}</td>
                    <td>{circuit.podiums}</td>
                    <td>{circuit.total_points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'dnfs' && dnfs && (
        <>
          <div className="driver-stats-section">
            <h3>DNF Overview</h3>
            <div className="stats-grid">
              <div className="stat-box">
                <span>Total Non-Finishes</span>
                <strong>{dnfs.total_non_finishes}</strong>
              </div>
            </div>
          </div>

          <div className="driver-results-section">
            <h3>DNF Breakdown by Status</h3>
            <div className="results-table-wrapper">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {dnfs.breakdown_by_status.map((item, index) => (
                    <tr key={index}>
                      <td>{item.status}</td>
                      <td>{item.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="driver-results-section">
            <h3>DNF Rate by Season</h3>
            <div className="results-table-wrapper">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Season</th>
                    <th>Entries</th>
                    <th>Non-Finishes</th>
                    <th>DNF Rate %</th>
                  </tr>
                </thead>
                <tbody>
                  {dnfs.dnf_rate_by_season.map((item, index) => (
                    <tr key={index}>
                      <td>{item.year}</td>
                      <td>{item.race_entries}</td>
                      <td>{item.non_finishes}</td>
                      <td>{item.dnf_rate_percent}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default DriverDetailsPage