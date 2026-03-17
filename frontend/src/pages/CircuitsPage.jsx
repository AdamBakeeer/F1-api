import { useEffect, useMemo, useState } from 'react'
import './CircuitsPage.css'
import CircuitDetailsPage from './CircuitDetailsPage'

function CircuitsPage({ token, currentUser }) {
  const [circuits, setCircuits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCircuitSlug, setSelectedCircuitSlug] = useState(null)

  const [view, setView] = useState('current') // current | all-time | season
  const [search, setSearch] = useState('')
  const [countryFilter, setCountryFilter] = useState('')
  const [season, setSeason] = useState('2024')

  const years = useMemo(() => {
    const list = []
    for (let y = 2024; y >= 1950; y--) list.push(y)
    return list
  }, [])

  const countries = useMemo(() => {
    const unique = [...new Set(circuits.map((item) => item.country).filter(Boolean))]
    return unique.sort()
  }, [circuits])

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchCircuits()
    }, 250)

    return () => clearTimeout(timeout)
  }, [view, search, countryFilter, season])

  const fetchCircuits = async () => {
    try {
      setLoading(true)
      setError('')

      let url = ''

      if (view === 'current') {
        url = 'http://127.0.0.1:8000/circuits/current'
      } else if (view === 'season') {
        url = `http://127.0.0.1:8000/circuits/season/${season}`
      } else {
        const params = new URLSearchParams()
        params.append('limit', '200')

        if (search.trim()) params.append('q', search.trim())
        if (countryFilter) params.append('country', countryFilter)

        url = `http://127.0.0.1:8000/circuits?${params.toString()}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch circuits')
      }

      setCircuits(data.data || [])
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const filteredCircuits = useMemo(() => {
    if (view === 'all-time') return circuits

    return circuits.filter((circuit) => {
      const term = search.toLowerCase()
      const matchesSearch =
        (circuit.name || '').toLowerCase().includes(term) ||
        (circuit.location || '').toLowerCase().includes(term) ||
        (circuit.country || '').toLowerCase().includes(term)

      const matchesCountry = !countryFilter || circuit.country === countryFilter

      return matchesSearch && matchesCountry
    })
  }, [circuits, search, countryFilter, view])

  const getHeaderTitle = () => {
    if (view === 'current') return 'Current Circuits'
    if (view === 'season') return `Season Circuits - ${season}`
    return 'All-Time Circuit Explorer'
  }

  const getHeaderText = () => {
    if (view === 'current') {
      return 'Browse the venues currently used in the latest Formula 1 season.'
    }
    if (view === 'season') {
      return 'Explore the circuits used in a selected Formula 1 season.'
    }
    return 'Explore all Formula 1 venues through a searchable global circuit explorer.'
  }

  if (selectedCircuitSlug) {
    return (
      <CircuitDetailsPage
        circuitSlug={selectedCircuitSlug}
        goBack={() => setSelectedCircuitSlug(null)}
        token={token}
        currentUser={currentUser}
      />
    )
  }

  return (
    <div className="circuits-page">
      <div className="circuits-header">
        <h2>{getHeaderTitle()}</h2>
        <p>{getHeaderText()}</p>
      </div>

      <div className="circuits-controls">
        <div className="circuits-tabs">
          <button
            className={view === 'current' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('current')}
          >
            Current
          </button>

          <button
            className={view === 'season' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('season')}
          >
            By Season
          </button>

          <button
            className={view === 'all-time' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('all-time')}
          >
            All Time
          </button>
        </div>

        <div className="circuits-filters">
          <input
            type="text"
            placeholder="Search circuit, location, country..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="circuits-search"
          />

          <select
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
            className="circuits-select"
          >
            <option value="">All Countries</option>
            {countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>

          {view === 'season' && (
            <select
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              className="circuits-select"
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {loading && <p className="circuits-message">Loading circuits...</p>}
      {error && <p className="circuits-message error">{error}</p>}

      {!loading && !error && (
        <div className="circuits-layout">
          <div className="circuits-list-panel">
            <div className="circuits-list-header">
              <h3>Venue Explorer</h3>
              <span>{filteredCircuits.length} circuit(s)</span>
            </div>

            <div className="circuits-list">
              {filteredCircuits.map((circuit) => (
                <button
                  key={circuit.circuit_id}
                  className="circuit-list-card"
                  onClick={() => setSelectedCircuitSlug(circuit.circuit_slug)}
                >
                  <div className="circuit-list-top-line"></div>
                  <h4>{circuit.name}</h4>
                  <p>{circuit.location || 'Unknown location'}</p>
                  <div className="circuit-meta-row">
                    <span>{circuit.country || 'N/A'}</span>
                    <span>{circuit.alt ?? 'N/A'} m</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="circuits-preview-panel">
            <div className="circuits-preview-box">
              <h3>How this page is different</h3>
              <p>
                Circuits focuses on venues, geography, and long-term performance
                at each track — not drivers, not teams, and not individual race weekends.
              </p>

              <div className="circuits-preview-grid">
                <div className="preview-stat">
                  <span>Venue Focus</span>
                  <strong>Track</strong>
                </div>
                <div className="preview-stat">
                  <span>Perspective</span>
                  <strong>Historical</strong>
                </div>
                <div className="preview-stat">
                  <span>Main Insight</span>
                  <strong>Who excels here</strong>
                </div>
                <div className="preview-stat">
                  <span>Data Type</span>
                  <strong>Venue Intelligence</strong>
                </div>
              </div>

              <p className="preview-note">
                Select a circuit from the left to open its full venue intelligence dashboard.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CircuitsPage