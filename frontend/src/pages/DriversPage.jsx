import { useEffect, useMemo, useState } from 'react'
import { API_BASE_URL } from '../config.js'
import './DriversPage.css'
import DriverDetailsPage from './DriverDetailsPage'

function DriversPage({ token, currentUser }) {
  const [drivers, setDrivers] = useState([])
  const [standings, setStandings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDriverSlug, setSelectedDriverSlug] = useState(null)

  const [view, setView] = useState('current')
  const [search, setSearch] = useState('')
  const [season, setSeason] = useState('2024')
  const [roundFilter, setRoundFilter] = useState('')
  const [nationalityFilter, setNationalityFilter] = useState('')

  const years = useMemo(() => {
    const list = []
    for (let y = 2024; y >= 1950; y--) list.push(y)
    return list
  }, [])

  const rounds = useMemo(() => {
    const list = []
    for (let r = 1; r <= 24; r++) list.push(r)
    return list
  }, [])

  const nationalities = useMemo(() => {
    const source = view === 'standings' ? standings : drivers
    const unique = [...new Set(source.map((item) => item.nationality).filter(Boolean))]
    return unique.sort()
  }, [drivers, standings, view])

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchData()
    }, 300)

    return () => clearTimeout(timeout)
  }, [view, season, roundFilter, search, nationalityFilter])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')

      let url = ''

      if (view === 'current') {
        url = `${API_BASE_URL}/drivers/current`
      } else if (view === 'all-time') {
        const params = new URLSearchParams()
        params.append('limit', '200')

        if (search.trim()) params.append('q', search.trim())
        if (nationalityFilter) params.append('nationality', nationalityFilter)

        url = `${API_BASE_URL}/drivers?${params.toString()}`
      } else if (view === 'standings') {
        const params = new URLSearchParams()
        if (roundFilter) params.append('round', roundFilter)

        const queryString = params.toString()
        url = queryString
          ? `${API_BASE_URL}/drivers/standings/${season}?${queryString}`
          : `${API_BASE_URL}/drivers/standings/${season}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch data')
      }

      if (view === 'standings') {
        setStandings(data.data || [])
        setDrivers([])
      } else {
        setDrivers(data.data || [])
        setStandings([])
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const filteredDrivers = useMemo(() => {
    if (view === 'all-time') return drivers

    return drivers.filter((driver) => {
      const fullName = `${driver.forename} ${driver.surname}`.toLowerCase()
      const code = (driver.code || '').toLowerCase()
      const nationality = (driver.nationality || '').toLowerCase()
      const term = search.toLowerCase()

      const matchesSearch =
        fullName.includes(term) ||
        code.includes(term) ||
        nationality.includes(term)

      const matchesNationality =
        !nationalityFilter || driver.nationality === nationalityFilter

      return matchesSearch && matchesNationality
    })
  }, [drivers, search, view, nationalityFilter])

  const filteredStandings = useMemo(() => {
    return standings.filter((driver) => {
      const fullName = `${driver.forename} ${driver.surname}`.toLowerCase()
      const code = (driver.code || '').toLowerCase()
      const nationality = (driver.nationality || '').toLowerCase()
      const term = search.toLowerCase()

      const matchesSearch =
        fullName.includes(term) ||
        code.includes(term) ||
        nationality.includes(term)

      const matchesNationality =
        !nationalityFilter || driver.nationality === nationalityFilter

      return matchesSearch && matchesNationality
    })
  }, [standings, search, nationalityFilter])

  const getHeaderTitle = () => {
    if (view === 'current') return 'Current Drivers'
    if (view === 'all-time') return 'All-Time Drivers'
    return roundFilter
      ? `Driver Standings - ${season} (After Round ${roundFilter})`
      : `Driver Standings - ${season}`
  }

  const getHeaderText = () => {
    if (view === 'current') {
      return 'Explore the active Formula 1 drivers currently represented in your backend API.'
    }
    if (view === 'all-time') {
      return 'Browse the historical driver database and explore the full Formula 1 archive.'
    }
    return 'View season standings in a clean, interactive format, including round-by-round progression.'
  }

  if (selectedDriverSlug) {
    return (
      <DriverDetailsPage
        driverSlug={selectedDriverSlug}
        goBack={() => setSelectedDriverSlug(null)}
        token={token}
        currentUser={currentUser}
      />
    )
  }

  return (
    <div className="drivers-page">
      <div className="drivers-header">
        <h2>{getHeaderTitle()}</h2>
        <p>{getHeaderText()}</p>
      </div>

      <div className="drivers-controls">
        <div className="drivers-tabs">
          <button
            className={view === 'current' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('current')}
          >
            Current
          </button>

          <button
            className={view === 'all-time' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('all-time')}
          >
            All Time
          </button>

          <button
            className={view === 'standings' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('standings')}
          >
            Standings
          </button>
        </div>

        <div className="drivers-filters">
          <input
            type="text"
            placeholder="Search by name, code, nationality..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="drivers-search"
          />

          <select
            value={nationalityFilter}
            onChange={(e) => setNationalityFilter(e.target.value)}
            className="drivers-select"
          >
            <option value="">All Nationalities</option>
            {nationalities.map((nationality) => (
              <option key={nationality} value={nationality}>
                {nationality}
              </option>
            ))}
          </select>

          {view === 'standings' && (
            <>
              <select
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                className="drivers-select"
              >
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>

              <select
                value={roundFilter}
                onChange={(e) => setRoundFilter(e.target.value)}
                className="drivers-select"
              >
                <option value="">All Rounds</option>
                {rounds.map((round) => (
                  <option key={round} value={round}>
                    Round {round}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>
      </div>

      {loading && <p className="drivers-message">Loading data...</p>}
      {error && <p className="drivers-message error">{error}</p>}

      {!loading && !error && view !== 'standings' && (
        <div className="drivers-grid">
          {filteredDrivers.map((driver) => (
            <div
              key={driver.driver_id}
              className="driver-card clickable-card"
              onClick={() => setSelectedDriverSlug(driver.driver_slug)}
            >
              <div className="driver-top-line"></div>

              <div className="driver-card-header">
                <h3>
                  {driver.forename} {driver.surname}
                </h3>
                {driver.code && <span className="driver-code-badge">{driver.code}</span>}
              </div>

              <p><strong>Nationality:</strong> {driver.nationality || 'N/A'}</p>
              <p><strong>Date of Birth:</strong> {driver.dob || 'N/A'}</p>
              <p><strong>Slug:</strong> {driver.driver_slug}</p>

              <button
                className="driver-view-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedDriverSlug(driver.driver_slug)
                }}
              >
                View Driver
              </button>
            </div>
          ))}
        </div>
      )}

      {!loading && !error && view === 'standings' && (
        <div className="standings-wrapper">
          <table className="standings-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Driver</th>
                <th>Code</th>
                <th>Nationality</th>
                <th>Points</th>
                <th>Wins</th>
                <th>Podiums</th>
                <th>Entries</th>
              </tr>
            </thead>
            <tbody>
              {filteredStandings.map((driver) => (
                <tr
                  key={driver.driver_id}
                  className="standings-row"
                  onClick={() => setSelectedDriverSlug(driver.driver_slug)}
                >
                  <td>{driver.position}</td>
                  <td>{driver.forename} {driver.surname}</td>
                  <td>{driver.code || 'N/A'}</td>
                  <td>{driver.nationality || 'N/A'}</td>
                  <td>{driver.points}</td>
                  <td>{driver.wins}</td>
                  <td>{driver.podiums}</td>
                  <td>{driver.race_entries}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default DriversPage