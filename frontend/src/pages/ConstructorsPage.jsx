import { useEffect, useMemo, useState } from 'react'
import './ConstructorsPage.css'
import ConstructorDetailsPage from './ConstructorDetailsPage'

function ConstructorsPage() {
  const [constructors, setConstructors] = useState([])
  const [standings, setStandings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedConstructorSlug, setSelectedConstructorSlug] = useState(null)

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
    const source = view === 'standings' ? standings : constructors
    const unique = [...new Set(source.map((item) => item.nationality).filter(Boolean))]
    return unique.sort()
  }, [constructors, standings, view])

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
        url = 'http://127.0.0.1:8000/constructors/current'
      } else if (view === 'all-time') {
        const params = new URLSearchParams()
        params.append('limit', '200')

        if (search.trim()) {
          params.append('q', search.trim())
        }

        if (nationalityFilter) {
          params.append('nationality', nationalityFilter)
        }

        url = `http://127.0.0.1:8000/constructors?${params.toString()}`
      } else if (view === 'standings') {
        const params = new URLSearchParams()

        if (roundFilter) {
          params.append('round', roundFilter)
        }

        const queryString = params.toString()
        url = queryString
          ? `http://127.0.0.1:8000/constructors/standings/${season}?${queryString}`
          : `http://127.0.0.1:8000/constructors/standings/${season}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch data')
      }

      if (view === 'standings') {
        setStandings(data.data || [])
        setConstructors([])
      } else {
        setConstructors(data.data || [])
        setStandings([])
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const filteredConstructors = useMemo(() => {
    if (view === 'all-time') {
      return constructors
    }

    return constructors.filter((constructor) => {
      const name = (constructor.name || '').toLowerCase()
      const nationality = (constructor.nationality || '').toLowerCase()
      const term = search.toLowerCase()

      const matchesSearch =
        name.includes(term) || nationality.includes(term)

      const matchesNationality =
        !nationalityFilter || constructor.nationality === nationalityFilter

      return matchesSearch && matchesNationality
    })
  }, [constructors, search, view, nationalityFilter])

  const filteredStandings = useMemo(() => {
    return standings.filter((constructor) => {
      const name = (constructor.name || '').toLowerCase()
      const nationality = (constructor.nationality || '').toLowerCase()
      const term = search.toLowerCase()

      const matchesSearch =
        name.includes(term) || nationality.includes(term)

      const matchesNationality =
        !nationalityFilter || constructor.nationality === nationalityFilter

      return matchesSearch && matchesNationality
    })
  }, [standings, search, nationalityFilter])

  const getHeaderTitle = () => {
    if (view === 'current') return 'Current Constructors'
    if (view === 'all-time') return 'All-Time Constructors'
    return roundFilter
      ? `Constructor Standings - ${season} (After Round ${roundFilter})`
      : `Constructor Standings - ${season}`
  }

  const getHeaderText = () => {
    if (view === 'current') {
      return 'Explore the active Formula 1 constructors currently represented in your backend API.'
    }
    if (view === 'all-time') {
      return 'Browse the historical constructor database and explore Formula 1 team history.'
    }
    return 'View constructor standings with season and round-based progression.'
  }

  if (selectedConstructorSlug) {
    return (
      <ConstructorDetailsPage
        constructorSlug={selectedConstructorSlug}
        goBack={() => setSelectedConstructorSlug(null)}
      />
    )
  }

  return (
    <div className="constructors-page">
      <div className="constructors-header">
        <h2>{getHeaderTitle()}</h2>
        <p>{getHeaderText()}</p>
      </div>

      <div className="constructors-controls">
        <div className="constructors-tabs">
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

        <div className="constructors-filters">
          <input
            type="text"
            placeholder="Search by team name or nationality..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="constructors-search"
          />

          <select
            value={nationalityFilter}
            onChange={(e) => setNationalityFilter(e.target.value)}
            className="constructors-select"
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
                className="constructors-select"
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
                className="constructors-select"
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

      {loading && <p className="constructors-message">Loading data...</p>}
      {error && <p className="constructors-message error">{error}</p>}

      {!loading && !error && view !== 'standings' && (
        <div className="constructors-grid">
          {filteredConstructors.map((constructor) => (
            <div
              key={constructor.constructor_id}
              className="constructor-card clickable-card"
              onClick={() => setSelectedConstructorSlug(constructor.constructor_slug)}
            >
              <div className="constructor-card-top-line"></div>

              <div className="constructor-card-header">
                <h3>{constructor.name}</h3>
              </div>

              <p><strong>Nationality:</strong> {constructor.nationality || 'N/A'}</p>
              <p><strong>Slug:</strong> {constructor.constructor_slug}</p>

              <button
                className="constructor-view-btn"
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedConstructorSlug(constructor.constructor_slug)
                }}
              >
                View Constructor
              </button>
            </div>
          ))}
        </div>
      )}

      {!loading && !error && view === 'standings' && (
        <div className="constructors-standings-wrapper">
          <table className="constructors-standings-table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Constructor</th>
                <th>Nationality</th>
                <th>Points</th>
                <th>Wins</th>
                <th>Podiums</th>
                <th>Entries</th>
              </tr>
            </thead>
            <tbody>
              {filteredStandings.map((constructor) => (
                <tr
                  key={constructor.constructor_id}
                  className="constructors-standings-row"
                  onClick={() => setSelectedConstructorSlug(constructor.constructor_slug)}
                >
                  <td>{constructor.position}</td>
                  <td>{constructor.name}</td>
                  <td>{constructor.nationality || 'N/A'}</td>
                  <td>{constructor.points}</td>
                  <td>{constructor.wins}</td>
                  <td>{constructor.podiums}</td>
                  <td>{constructor.race_entries}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default ConstructorsPage