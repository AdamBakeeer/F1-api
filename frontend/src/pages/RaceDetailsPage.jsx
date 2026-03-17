import { useEffect, useMemo, useState } from 'react'
import './RaceDetailsPage.css'

function RaceDetailsPage({ year, round, goBack }) {
  const [race, setRace] = useState(null)
  const [summary, setSummary] = useState(null)
  const [podium, setPodium] = useState([])
  const [results, setResults] = useState([])
  const [dnfs, setDnfs] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('results') // overview | results | dnfs
  const [showOnlyDnfs, setShowOnlyDnfs] = useState(false)

  useEffect(() => {
    fetchRaceData()
  }, [year, round])

  const fetchRaceData = async () => {
    try {
      setLoading(true)
      setError('')

      const [raceRes, summaryRes, podiumRes, resultsRes, dnfsRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/races/${year}/${round}`),
        fetch(`http://127.0.0.1:8000/races/${year}/${round}/summary`),
        fetch(`http://127.0.0.1:8000/races/${year}/${round}/podium`),
        fetch(`http://127.0.0.1:8000/races/${year}/${round}/results`),
        fetch(`http://127.0.0.1:8000/races/${year}/${round}/dnfs`)
      ])

      const raceData = await raceRes.json()
      const summaryData = await summaryRes.json()
      const podiumData = await podiumRes.json()
      const resultsData = await resultsRes.json()
      const dnfsData = await dnfsRes.json()

      if (!raceRes.ok) throw new Error(raceData.detail || 'Failed to load race')
      if (!summaryRes.ok) throw new Error(summaryData.detail || 'Failed to load summary')
      if (!podiumRes.ok) throw new Error(podiumData.detail || 'Failed to load podium')
      if (!resultsRes.ok) throw new Error(resultsData.detail || 'Failed to load results')
      if (!dnfsRes.ok) throw new Error(dnfsData.detail || 'Failed to load DNFs')

      setRace(raceData)
      setSummary(summaryData)
      setPodium(podiumData.data || [])
      setResults(resultsData.data || [])
      setDnfs(dnfsData)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const winner = summary?.winner || null

  const filteredResults = useMemo(() => {
    if (!showOnlyDnfs) return results
    return results.filter((item) => {
      const status = (item.status || '').toLowerCase()
      return !(status === 'finished' || status.startsWith('+'))
    })
  }, [results, showOnlyDnfs])

  const getRowClass = (item) => {
    const pos = Number(item.position_order)
    const status = (item.status || '').toLowerCase()

    if (!(status === 'finished' || status.startsWith('+'))) return 'race-row-dnf'
    if (pos === 1) return 'race-row-p1'
    if (pos === 2) return 'race-row-p2'
    if (pos === 3) return 'race-row-p3'
    return ''
  }

  if (loading) {
    return (
      <div className="race-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Races</button>
        <p className="race-details-message">Loading race details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="race-details-page">
        <button className="back-btn" onClick={goBack}>← Back to Races</button>
        <p className="race-details-message error">{error}</p>
      </div>
    )
  }

  return (
    <div className="race-details-page">
      <button className="back-btn" onClick={goBack}>← Back to Races</button>

      {race && (
        <>
          <div className="race-event-banner">
            <div className="race-banner-cell">
              <span>Season</span>
              <strong>{race.year}</strong>
            </div>
            <div className="race-banner-cell">
              <span>Round</span>
              <strong>{race.round}</strong>
            </div>
            <div className="race-banner-cell">
              <span>Date</span>
              <strong>{race.date}</strong>
            </div>
            <div className="race-banner-cell">
              <span>Circuit</span>
              <strong>{race.circuit_name}</strong>
            </div>
            <div className="race-banner-cell">
              <span>Location</span>
              <strong>{race.country}</strong>
            </div>
          </div>

          <div className="race-header-card">
            <div className="race-header-top-line"></div>
            <h2>{race.name}</h2>
            <p className="race-header-subtitle">
              {race.circuit_name} · {race.location}, {race.country}
            </p>
          </div>
        </>
      )}

      <div className="race-quick-insights">
        <div className="race-insight-card">
          <span>Winner</span>
          <strong>{winner ? `${winner.forename} ${winner.surname}` : 'N/A'}</strong>
        </div>
        <div className="race-insight-card">
          <span>Winning Team</span>
          <strong>{winner?.constructor_name || 'N/A'}</strong>
        </div>
        <div className="race-insight-card">
          <span>Finishers</span>
          <strong>{summary?.summary?.finishers_like ?? 'N/A'}</strong>
        </div>
        <div className="race-insight-card dnf-accent">
          <span>DNFs</span>
          <strong>{summary?.summary?.non_finishers ?? 0}</strong>
        </div>
      </div>

      {winner && (
        <div className="winner-spotlight">
          <div className="winner-spotlight-top-line"></div>
          <div className="winner-spotlight-content">
            <div className="winner-left">
              <span className="winner-label">Race Winner</span>
              <h3>{winner.forename} {winner.surname}</h3>
              <p>{winner.constructor_name}</p>
            </div>
            <div className="winner-right">
              <div className="winner-mini-stat">
                <span>Driver Code</span>
                <strong>{winner.code || 'N/A'}</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="race-tabs">
        <button
          className={activeTab === 'overview' ? 'race-tab active-race-tab' : 'race-tab'}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'results' ? 'race-tab active-race-tab' : 'race-tab'}
          onClick={() => setActiveTab('results')}
        >
          Results
        </button>
        <button
          className={activeTab === 'dnfs' ? 'race-tab active-race-tab' : 'race-tab'}
          onClick={() => setActiveTab('dnfs')}
        >
          DNFs
        </button>
      </div>

      {activeTab === 'overview' && (
        <>
          <div className="race-podium-section">
            <h3>Podium</h3>
            <div className="race-podium-layout">
              {podium.find((p) => p.position_order === 2) && (
                <div className="race-podium-card silver-card">
                  <div className="podium-rank">P2</div>
                  <h4>
                    {podium.find((p) => p.position_order === 2).forename}{' '}
                    {podium.find((p) => p.position_order === 2).surname}
                  </h4>
                  <p>{podium.find((p) => p.position_order === 2).constructor_name}</p>
                  <p><strong>Grid:</strong> {podium.find((p) => p.position_order === 2).grid}</p>
                  <p><strong>Points:</strong> {podium.find((p) => p.position_order === 2).points}</p>
                </div>
              )}

              {podium.find((p) => p.position_order === 1) && (
                <div className="race-podium-card winner-card">
                  <div className="podium-rank">P1</div>
                  <h4>
                    {podium.find((p) => p.position_order === 1).forename}{' '}
                    {podium.find((p) => p.position_order === 1).surname}
                  </h4>
                  <p>{podium.find((p) => p.position_order === 1).constructor_name}</p>
                  <p><strong>Grid:</strong> {podium.find((p) => p.position_order === 1).grid}</p>
                  <p><strong>Points:</strong> {podium.find((p) => p.position_order === 1).points}</p>
                </div>
              )}

              {podium.find((p) => p.position_order === 3) && (
                <div className="race-podium-card bronze-card">
                  <div className="podium-rank">P3</div>
                  <h4>
                    {podium.find((p) => p.position_order === 3).forename}{' '}
                    {podium.find((p) => p.position_order === 3).surname}
                  </h4>
                  <p>{podium.find((p) => p.position_order === 3).constructor_name}</p>
                  <p><strong>Grid:</strong> {podium.find((p) => p.position_order === 3).grid}</p>
                  <p><strong>Points:</strong> {podium.find((p) => p.position_order === 3).points}</p>
                </div>
              )}
            </div>
          </div>

          <div className="race-summary-section">
            <h3>Event Summary</h3>
            <div className="race-summary-grid">
              <div className="race-summary-box">
                <span>Total Classified Rows</span>
                <strong>{summary?.summary?.total_classified_rows ?? 'N/A'}</strong>
              </div>
              <div className="race-summary-box">
                <span>Finishers</span>
                <strong>{summary?.summary?.finishers_like ?? 'N/A'}</strong>
              </div>
              <div className="race-summary-box">
                <span>Non-Finishers</span>
                <strong>{summary?.summary?.non_finishers ?? 'N/A'}</strong>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'results' && (
        <div className="race-results-section">
          <div className="race-section-header">
            <h3>Full Results</h3>
            <label className="results-toggle">
              <input
                type="checkbox"
                checked={showOnlyDnfs}
                onChange={() => setShowOnlyDnfs(!showOnlyDnfs)}
              />
              <span>Show DNFs only</span>
            </label>
          </div>

          <div className="race-table-wrapper">
            <table className="race-table">
              <thead>
                <tr>
                  <th>Pos</th>
                  <th>Driver</th>
                  <th>Code</th>
                  <th>Team</th>
                  <th>Grid</th>
                  <th>Laps</th>
                  <th>Points</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((item) => (
                  <tr key={item.result_id} className={getRowClass(item)}>
                    <td>{item.position_order || 'N/A'}</td>
                    <td>{item.forename} {item.surname}</td>
                    <td>{item.code || 'N/A'}</td>
                    <td>{item.constructor_name}</td>
                    <td>{item.grid}</td>
                    <td>{item.laps}</td>
                    <td>{item.points}</td>
                    <td>{item.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'dnfs' && dnfs && (
        <div className="race-dnfs-section">
          <h3>Retirements & DNFs</h3>

          <div className="race-summary-grid">
            <div className="race-summary-box dnf-accent-box">
              <span>Total DNFs</span>
              <strong>{dnfs.non_finishers_count}</strong>
            </div>
          </div>

          <div className="race-table-wrapper">
            <table className="race-table">
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Code</th>
                  <th>Team</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {dnfs.non_finishers.map((item, index) => (
                  <tr key={index} className="race-row-dnf">
                    <td>{item.forename} {item.surname}</td>
                    <td>{item.code || 'N/A'}</td>
                    <td>{item.constructor_name}</td>
                    <td>{item.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="race-breakdown-block">
            <h4>Status Breakdown</h4>
            <div className="race-breakdown-grid">
              {dnfs.breakdown_by_status.map((item, index) => (
                <div key={index} className="race-breakdown-card">
                  <span>{item.status}</span>
                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RaceDetailsPage