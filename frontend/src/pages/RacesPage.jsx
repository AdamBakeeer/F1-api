import { useEffect, useMemo, useState } from 'react'
import './RacesPage.css'

function RacesPage() {
  const [latestSeason, setLatestSeason] = useState('2024')
  const [season, setSeason] = useState('2024')

  const [leftTab, setLeftTab] = useState('calendar') // calendar | winners
  const [rightTab, setRightTab] = useState('overview') // overview | podium | results | dnfs

  const [search, setSearch] = useState('')
  const [countryFilter, setCountryFilter] = useState('')

  const [seasonRaces, setSeasonRaces] = useState([])
  const [calendar, setCalendar] = useState([])
  const [winners, setWinners] = useState([])

  const [selectedRace, setSelectedRace] = useState(null)
  const [raceSummary, setRaceSummary] = useState(null)
  const [racePodium, setRacePodium] = useState([])
  const [raceResults, setRaceResults] = useState([])
  const [raceDnfs, setRaceDnfs] = useState(null)

  const [loadingSeason, setLoadingSeason] = useState(true)
  const [loadingRace, setLoadingRace] = useState(false)
  const [error, setError] = useState('')

  const years = useMemo(() => {
    const list = []
    for (let y = 2024; y >= 1950; y--) list.push(y)
    return list
  }, [])

  useEffect(() => {
    fetchLatestSeason()
  }, [])

  useEffect(() => {
    fetchSeasonData()
  }, [season])

  const fetchLatestSeason = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/races/current')
      const data = await response.json()

      if (response.ok && data.season) {
        setLatestSeason(String(data.season))
        setSeason(String(data.season))
      }
    } catch {
      // silent fallback
    }
  }

  const fetchSeasonData = async () => {
    try {
      setLoadingSeason(true)
      setError('')

      const [seasonRes, calendarRes, winnersRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/races/season/${season}`),
        fetch(`http://127.0.0.1:8000/races/season/${season}/calendar`),
        fetch(`http://127.0.0.1:8000/races/season/${season}/winners`)
      ])

      const seasonData = await seasonRes.json()
      const calendarData = await calendarRes.json()
      const winnersData = await winnersRes.json()

      if (!seasonRes.ok) throw new Error(seasonData.detail || 'Failed to load season races')
      if (!calendarRes.ok) throw new Error(calendarData.detail || 'Failed to load calendar')
      if (!winnersRes.ok) throw new Error(winnersData.detail || 'Failed to load winners')

      setSeasonRaces(seasonData.data || [])
      setCalendar(calendarData.data || [])
      setWinners(winnersData.data || [])

      if ((seasonData.data || []).length > 0) {
        const firstRace = seasonData.data[0]
        fetchRaceDetails(Number(season), firstRace.round)
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoadingSeason(false)
    }
  }

  const fetchRaceDetails = async (year, round) => {
    try {
      setLoadingRace(true)
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

      setSelectedRace(raceData)
      setRaceSummary(summaryData)
      setRacePodium(podiumData.data || [])
      setRaceResults(resultsData.data || [])
      setRaceDnfs(dnfsData)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoadingRace(false)
    }
  }

  const totalRaces = seasonRaces.length
  const uniqueCountries = useMemo(() => {
    return new Set(seasonRaces.map((race) => race.country).filter(Boolean)).size
  }, [seasonRaces])

  const uniqueCircuits = useMemo(() => {
    return new Set(seasonRaces.map((race) => race.circuit_id).filter(Boolean)).size
  }, [seasonRaces])

  const totalDnfCount = raceDnfs?.non_finishers_count ?? 0

  const availableCountries = useMemo(() => {
    const source = leftTab === 'calendar' ? calendar : winners
    const unique = [...new Set(source.map((item) => item.country).filter(Boolean))]
    return unique.sort()
  }, [calendar, winners, leftTab])

  const filteredCalendar = useMemo(() => {
    return calendar.filter((race) => {
      const term = search.toLowerCase()
      const matchesSearch =
        (race.race_name || '').toLowerCase().includes(term) ||
        (race.circuit_name || '').toLowerCase().includes(term) ||
        (race.location || '').toLowerCase().includes(term) ||
        (race.country || '').toLowerCase().includes(term)

      const matchesCountry = !countryFilter || race.country === countryFilter
      return matchesSearch && matchesCountry
    })
  }, [calendar, search, countryFilter])

  const filteredWinners = useMemo(() => {
    return winners.filter((race) => {
      const term = search.toLowerCase()
      const matchesSearch =
        (race.race_name || '').toLowerCase().includes(term) ||
        (`${race.forename} ${race.surname}` || '').toLowerCase().includes(term) ||
        (race.constructor_name || '').toLowerCase().includes(term)

      const matchesCountry = !countryFilter || race.country === countryFilter
      return matchesSearch && matchesCountry
    })
  }, [winners, search, countryFilter])

  const getResultRowClass = (item) => {
    const pos = Number(item.position_order)
    const status = (item.status || '').toLowerCase()

    if (!(status === 'finished' || status.startsWith('+'))) return 'result-row-dnf'
    if (pos <= 3) return 'result-row-podium'
    return ''
  }

  return (
    <div className="races-page unique-races-page">
      <div className="races-hero">
        <div className="races-hero-left">
          <div className="season-chip">Latest Season: {latestSeason}</div>
          <h2>Race Command Center</h2>
          <p>
            Explore the calendar, race winners, podiums, full classifications,
            and retirements for every race weekend.
          </p>
        </div>

        <div className="races-hero-right">
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="races-select"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadingSeason && <p className="races-message">Loading season data...</p>}
      {error && <p className="races-message error">{error}</p>}

      {!loadingSeason && !error && (
        <>
          <div className="season-overview-grid">
            <div className="overview-stat-card">
              <span>Total Races</span>
              <strong>{totalRaces}</strong>
            </div>
            <div className="overview-stat-card">
              <span>Circuits Used</span>
              <strong>{uniqueCircuits}</strong>
            </div>
            <div className="overview-stat-card">
              <span>Countries</span>
              <strong>{uniqueCountries}</strong>
            </div>
            <div className="overview-stat-card">
              <span>Selected Round</span>
              <strong>{selectedRace?.round || '-'}</strong>
            </div>
            <div className="overview-stat-card">
              <span>Selected Winner</span>
              <strong>
                {raceSummary?.winner
                  ? `${raceSummary.winner.forename} ${raceSummary.winner.surname}`
                  : 'N/A'}
              </strong>
            </div>
            <div className="overview-stat-card danger-card">
              <span>Selected Race DNFs</span>
              <strong>{totalDnfCount}</strong>
            </div>
          </div>

          <div className="featured-race-banner">
            <div className="featured-race-left">
              <span className="featured-label">Selected Race</span>
              <h3>{selectedRace?.name || 'Choose a race'}</h3>
              <p>
                {selectedRace
                  ? `${selectedRace.circuit_name} · ${selectedRace.location}, ${selectedRace.country}`
                  : 'Select a race to unlock the full dashboard.'}
              </p>
            </div>

            <div className="featured-race-right">
              <div className="featured-mini">
                <span>Round</span>
                <strong>{selectedRace?.round || '-'}</strong>
              </div>
              <div className="featured-mini">
                <span>Date</span>
                <strong>{selectedRace?.date || '-'}</strong>
              </div>
            </div>
          </div>

          <div className="races-dashboard-layout">
            <div className="races-left-panel">
              <div className="races-panel-header">
                <div className="races-panel-tabs">
                  <button
                    className={leftTab === 'calendar' ? 'race-tab active-race-tab' : 'race-tab'}
                    onClick={() => setLeftTab('calendar')}
                  >
                    Calendar
                  </button>
                  <button
                    className={leftTab === 'winners' ? 'race-tab active-race-tab' : 'race-tab'}
                    onClick={() => setLeftTab('winners')}
                  >
                    Winners
                  </button>
                </div>

                <div className="races-panel-filters">
                  <input
                    type="text"
                    placeholder={
                      leftTab === 'calendar'
                        ? 'Search race, circuit, location...'
                        : 'Search race, winner, team...'
                    }
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="races-search"
                  />

                  <select
                    value={countryFilter}
                    onChange={(e) => setCountryFilter(e.target.value)}
                    className="races-select"
                  >
                    <option value="">All Countries</option>
                    {availableCountries.map((country) => (
                      <option key={country} value={country}>
                        {country}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {leftTab === 'calendar' && (
                <div className="race-list-table-wrapper">
                  <table className="race-list-table">
                    <thead>
                      <tr>
                        <th>Rnd</th>
                        <th>Race</th>
                        <th>Date</th>
                        <th>Circuit</th>
                        <th>Country</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCalendar.map((race) => (
                        <tr
                          key={race.race_id}
                          className={
                            selectedRace?.round === race.round
                              ? 'race-list-row selected-race-row'
                              : 'race-list-row'
                          }
                          onClick={() => fetchRaceDetails(Number(season), race.round)}
                        >
                          <td>{race.round}</td>
                          <td>{race.race_name}</td>
                          <td>{race.date}</td>
                          <td>{race.circuit_name}</td>
                          <td>{race.country}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {leftTab === 'winners' && (
                <div className="race-list-table-wrapper">
                  <table className="race-list-table">
                    <thead>
                      <tr>
                        <th>Rnd</th>
                        <th>Race</th>
                        <th>Winner</th>
                        <th>Code</th>
                        <th>Team</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredWinners.map((race) => (
                        <tr
                          key={race.race_id}
                          className={
                            selectedRace?.round === race.round
                              ? 'race-list-row selected-race-row'
                              : 'race-list-row'
                          }
                          onClick={() => fetchRaceDetails(Number(season), race.round)}
                        >
                          <td>{race.round}</td>
                          <td>{race.race_name}</td>
                          <td>{race.forename} {race.surname}</td>
                          <td>{race.code || 'N/A'}</td>
                          <td>{race.constructor_name}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="races-right-panel">
              <div className="races-right-tabs">
                <button
                  className={rightTab === 'overview' ? 'race-tab active-race-tab' : 'race-tab'}
                  onClick={() => setRightTab('overview')}
                >
                  Overview
                </button>
                <button
                  className={rightTab === 'podium' ? 'race-tab active-race-tab' : 'race-tab'}
                  onClick={() => setRightTab('podium')}
                >
                  Podium
                </button>
                <button
                  className={rightTab === 'results' ? 'race-tab active-race-tab' : 'race-tab'}
                  onClick={() => setRightTab('results')}
                >
                  Results
                </button>
                <button
                  className={rightTab === 'dnfs' ? 'race-tab active-race-tab' : 'race-tab'}
                  onClick={() => setRightTab('dnfs')}
                >
                  DNFs
                </button>
              </div>

              {loadingRace && <p className="races-message">Loading race dashboard...</p>}

              {!loadingRace && selectedRace && rightTab === 'overview' && (
                <div className="race-dashboard-section">
                  <div className="race-dashboard-card">
                    <h3>{selectedRace.name}</h3>
                    <p>{selectedRace.circuit_name} · {selectedRace.location}, {selectedRace.country}</p>
                  </div>

                  <div className="season-overview-grid compact-grid">
                    <div className="overview-stat-card">
                      <span>Winner</span>
                      <strong>
                        {raceSummary?.winner
                          ? `${raceSummary.winner.forename} ${raceSummary.winner.surname}`
                          : 'N/A'}
                      </strong>
                    </div>
                    <div className="overview-stat-card">
                      <span>Winning Team</span>
                      <strong>{raceSummary?.winner?.constructor_name || 'N/A'}</strong>
                    </div>
                    <div className="overview-stat-card">
                      <span>Finishers</span>
                      <strong>{raceSummary?.summary?.finishers_like ?? 'N/A'}</strong>
                    </div>
                    <div className="overview-stat-card danger-card">
                      <span>DNFs</span>
                      <strong>{raceSummary?.summary?.non_finishers ?? 'N/A'}</strong>
                    </div>
                  </div>
                </div>
              )}

              {!loadingRace && selectedRace && rightTab === 'podium' && (
                <div className="podium-stack">
                  {racePodium.map((item) => (
                    <div
                      key={item.position_order}
                      className={`podium-feature-card podium-rank-${item.position_order}`}
                    >
                      <div className="podium-badge">P{item.position_order}</div>
                      <h4>{item.forename} {item.surname}</h4>
                      <p>{item.constructor_name}</p>
                      <div className="podium-meta">
                        <span>Grid {item.grid}</span>
                        <span>{item.points} pts</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {!loadingRace && selectedRace && rightTab === 'results' && (
                <div className="race-list-table-wrapper">
                  <table className="race-list-table">
                    <thead>
                      <tr>
                        <th>Pos</th>
                        <th>Driver</th>
                        <th>Code</th>
                        <th>Team</th>
                        <th>Grid</th>
                        <th>Laps</th>
                        <th>Pts</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {raceResults.map((item) => (
                        <tr key={item.result_id} className={getResultRowClass(item)}>
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
              )}

              {!loadingRace && selectedRace && rightTab === 'dnfs' && raceDnfs && (
                <div className="race-dashboard-section">
                  <div className="season-overview-grid compact-grid">
                    <div className="overview-stat-card danger-card">
                      <span>Total DNFs</span>
                      <strong>{raceDnfs.non_finishers_count}</strong>
                    </div>
                  </div>

                  <div className="race-list-table-wrapper">
                    <table className="race-list-table">
                      <thead>
                        <tr>
                          <th>Driver</th>
                          <th>Code</th>
                          <th>Team</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {raceDnfs.non_finishers.map((item, index) => (
                          <tr key={index} className="result-row-dnf">
                            <td>{item.forename} {item.surname}</td>
                            <td>{item.code || 'N/A'}</td>
                            <td>{item.constructor_name}</td>
                            <td>{item.status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="breakdown-chip-grid">
                    {raceDnfs.breakdown_by_status.map((item, index) => (
                      <div key={index} className="breakdown-chip-card">
                        <span>{item.status}</span>
                        <strong>{item.count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default RacesPage