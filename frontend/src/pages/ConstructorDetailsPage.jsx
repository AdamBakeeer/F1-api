import { useEffect, useMemo, useState } from 'react'
import './ConstructorDetailsPage.css'

function ConstructorDetailsPage({ constructorSlug, goBack }) {
  const [constructorData, setConstructorData] = useState(null)
  const [stats, setStats] = useState(null)
  const [drivers, setDrivers] = useState([])
  const [seasons, setSeasons] = useState([])
  const [bestCircuits, setBestCircuits] = useState([])
  const [dnfs, setDnfs] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedSeason, setSelectedSeason] = useState('')

  useEffect(() => {
    fetchConstructorData()
  }, [constructorSlug])

  useEffect(() => {
    if (constructorSlug) {
      fetchDrivers()
    }
  }, [constructorSlug, selectedSeason])

  const fetchConstructorData = async () => {
    try {
      setLoading(true)
      setError('')

      const [
        constructorRes,
        statsRes,
        seasonsRes,
        circuitsRes,
        dnfsRes
      ] = await Promise.all([
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/stats`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/seasons`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/best-circuits?limit=5`),
        fetch(`http://127.0.0.1:8000/constructors/${constructorSlug}/dnfs`)
      ])

      const constructorJson = await constructorRes.json()
      const statsJson = await statsRes.json()
      const seasonsJson = await seasonsRes.json()
      const circuitsJson = await circuitsRes.json()
      const dnfsJson = await dnfsRes.json()

      if (!constructorRes.ok) throw new Error(constructorJson.detail || 'Failed to load constructor')
      if (!statsRes.ok) throw new Error(statsJson.detail || 'Failed to load stats')
      if (!seasonsRes.ok) throw new Error(seasonsJson.detail || 'Failed to load seasons')
      if (!circuitsRes.ok) throw new Error(circuitsJson.detail || 'Failed to load best circuits')
      if (!dnfsRes.ok) throw new Error(dnfsJson.detail || 'Failed to load DNF data')

      setConstructorData(constructorJson)
      setStats(statsJson.data)
      setSeasons(seasonsJson.data || [])
      setBestCircuits(circuitsJson.data || [])
      setDnfs(dnfsJson)

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

  const fetchDrivers = async () => {
    try {
      let url = `http://127.0.0.1:8000/constructors/${constructorSlug}/drivers`

      if (selectedSeason) {
        url += `?year=${selectedSeason}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to load drivers')
      }

      setDrivers(data.data || [])
    } catch {
      setDrivers([])
    }
  }

  const seasonOptions = useMemo(() => {
    return seasons.map((item) => String(item.year))
  }, [seasons])

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
        </div>
      )}

      <div className="details-tabs">
        <button className={activeTab === 'overview' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={activeTab === 'drivers' ? 'details-tab active-details-tab' : 'details-tab'} onClick={() => setActiveTab('drivers')}>
          Drivers
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
            <div className="constructor-stats-section">
              <h3>Constructor Statistics</h3>
              <div className="constructor-stats-grid">
                <div className="constructor-stat-box"><span>Race Entries</span><strong>{stats.race_entries}</strong></div>
                <div className="constructor-stat-box"><span>Total Points</span><strong>{stats.total_points}</strong></div>
                <div className="constructor-stat-box"><span>Wins</span><strong>{stats.wins}</strong></div>
                <div className="constructor-stat-box"><span>Podiums</span><strong>{stats.podiums}</strong></div>
                <div className="constructor-stat-box"><span>First Season</span><strong>{stats.first_season}</strong></div>
                <div className="constructor-stat-box"><span>Last Season</span><strong>{stats.last_season}</strong></div>
              </div>
            </div>
          )}

          <div className="constructor-data-section">
            <h3>Season History</h3>
            <div className="constructor-table-wrapper">
              <table className="constructor-table">
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

      {activeTab === 'drivers' && (
        <div className="constructor-data-section">
          <div className="constructor-section-header">
            <h3>Drivers</h3>
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
          </div>

          <div className="constructor-table-wrapper">
            <table className="constructor-table">
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Code</th>
                  <th>Nationality</th>
                  <th>Entries</th>
                  <th>Points</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                </tr>
              </thead>
              <tbody>
                {drivers.map((driver, index) => (
                  <tr key={index}>
                    <td>{driver.forename} {driver.surname}</td>
                    <td>{driver.code || 'N/A'}</td>
                    <td>{driver.nationality || 'N/A'}</td>
                    <td>{driver.race_entries}</td>
                    <td>{driver.total_points}</td>
                    <td>{driver.wins}</td>
                    <td>{driver.podiums}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'circuits' && (
        <div className="constructor-data-section">
          <h3>Best Circuits</h3>
          <div className="constructor-circuit-grid">
            {bestCircuits.map((circuit, index) => (
              <div key={index} className="constructor-circuit-card">
                <div className="constructor-circuit-top-line"></div>
                <h4>{circuit.circuit_name}</h4>
                <p>{circuit.location}, {circuit.country}</p>
                <p><strong>Entries:</strong> {circuit.race_entries}</p>
                <p><strong>Wins:</strong> {circuit.wins}</p>
                <p><strong>Podiums:</strong> {circuit.podiums}</p>
                <p><strong>Points:</strong> {circuit.total_points}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'dnfs' && dnfs && (
        <>
          <div className="constructor-stats-section">
            <h3>DNF Overview</h3>
            <div className="constructor-stats-grid">
              <div className="constructor-stat-box">
                <span>Total Non-Finishes</span>
                <strong>{dnfs.total_non_finishes}</strong>
              </div>
            </div>
          </div>

          <div className="constructor-data-section">
            <h3>DNF Breakdown by Status</h3>
            <div className="constructor-table-wrapper">
              <table className="constructor-table">
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

          <div className="constructor-data-section">
            <h3>DNF Rate by Season</h3>
            <div className="constructor-table-wrapper">
              <table className="constructor-table">
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

export default ConstructorDetailsPage