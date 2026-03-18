import { useEffect, useMemo, useState } from 'react'
import { API_BASE_URL } from '../config.js'
import './AnalyticsPage.css'

function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [season, setSeason] = useState('2024')
  const [metric, setMetric] = useState('wins')

  const [dnfsBySeason, setDnfsBySeason] = useState([])
  const [topDrivers, setTopDrivers] = useState([])
  const [topConstructors, setTopConstructors] = useState([])
  const [circuitSpecialists, setCircuitSpecialists] = useState([])
  const [championshipBattles, setChampionshipBattles] = useState([])
  const [closestTitleFights, setClosestTitleFights] = useState([])
  const [comebackDrivers, setComebackDrivers] = useState([])
  const [constructorsByEra, setConstructorsByEra] = useState([])
  const [circuitDifficulty, setCircuitDifficulty] = useState([])
  const [titleFightProgression, setTitleFightProgression] = useState([])
  const [teammateBattles, setTeammateBattles] = useState([])
  const [driverRivalries, setDriverRivalries] = useState([])

  const years = useMemo(() => {
    const list = []
    for (let y = 2024; y >= 1950; y--) list.push(y)
    return list
  }, [])

  useEffect(() => {
    fetchAnalyticsData()
  }, [season, metric])

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      setError('')

      const [
        dnfsRes,
        driversRes,
        constructorsRes,
        specialistsRes,
        battlesRes,
        closeFightsRes,
        comebackRes,
        eraRes,
        difficultyRes,
        progressionRes,
        teammateRes,
        rivalriesRes
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/analytics/dnfs/by-season`),
        fetch(`${API_BASE_URL}/analytics/most-successful-drivers?metric=${metric}&limit=10`),
        fetch(`${API_BASE_URL}/analytics/most-successful-constructors?metric=${metric}&limit=10`),
        fetch(`${API_BASE_URL}/analytics/circuit-specialists?metric=${metric}&limit=10`),
        fetch(`${API_BASE_URL}/analytics/championship-battles/${season}?top_n=5`),
        fetch(`${API_BASE_URL}/analytics/closest-title-fights?limit=10`),
        fetch(`${API_BASE_URL}/analytics/comeback-drivers?limit=10&min_races=20`),
        fetch(`${API_BASE_URL}/analytics/constructors-by-era?limit=30`),
        fetch(`${API_BASE_URL}/analytics/circuit-difficulty?limit=10&min_races=3`),
        fetch(`${API_BASE_URL}/analytics/title-fight-progression/${season}?top_n=3`),
        fetch(`${API_BASE_URL}/analytics/teammate-battles/${season}?limit=20`),
        fetch(`${API_BASE_URL}/analytics/driver-rivalries?limit=20&min_shared_races=10`)
      ])

      const [
        dnfsData,
        driversData,
        constructorsData,
        specialistsData,
        battlesData,
        closeFightsData,
        comebackData,
        eraData,
        difficultyData,
        progressionData,
        teammateData,
        rivalriesData
      ] = await Promise.all([
        dnfsRes.json(),
        driversRes.json(),
        constructorsRes.json(),
        specialistsRes.json(),
        battlesRes.json(),
        closeFightsRes.json(),
        comebackRes.json(),
        eraRes.json(),
        difficultyRes.json(),
        progressionRes.json(),
        teammateRes.json(),
        rivalriesRes.json()
      ])

      if (!dnfsRes.ok) throw new Error(dnfsData.detail || 'Failed to load DNF trends')
      if (!driversRes.ok) throw new Error(driversData.detail || 'Failed to load drivers analytics')
      if (!constructorsRes.ok) throw new Error(constructorsData.detail || 'Failed to load constructors analytics')
      if (!specialistsRes.ok) throw new Error(specialistsData.detail || 'Failed to load circuit specialists')
      if (!battlesRes.ok) throw new Error(battlesData.detail || 'Failed to load championship battles')
      if (!closeFightsRes.ok) throw new Error(closeFightsData.detail || 'Failed to load title fights')
      if (!comebackRes.ok) throw new Error(comebackData.detail || 'Failed to load comeback drivers')
      if (!eraRes.ok) throw new Error(eraData.detail || 'Failed to load constructors by era')
      if (!difficultyRes.ok) throw new Error(difficultyData.detail || 'Failed to load circuit difficulty')
      if (!progressionRes.ok) throw new Error(progressionData.detail || 'Failed to load title fight progression')
      if (!teammateRes.ok) throw new Error(teammateData.detail || 'Failed to load teammate battles')
      if (!rivalriesRes.ok) throw new Error(rivalriesData.detail || 'Failed to load driver rivalries')

      setDnfsBySeason(dnfsData.data || [])
      setTopDrivers(driversData.data || [])
      setTopConstructors(constructorsData.data || [])
      setCircuitSpecialists(specialistsData.data || [])
      setChampionshipBattles(battlesData.data || [])
      setClosestTitleFights(closeFightsData.data || [])
      setComebackDrivers(comebackData.data || [])
      setConstructorsByEra(eraData.data || [])
      setCircuitDifficulty(difficultyData.data || [])
      setTitleFightProgression(progressionData.data || [])
      setTeammateBattles(teammateData.data || [])
      setDriverRivalries(rivalriesData.data || [])
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const overviewStats = useMemo(() => {
    const latestDnf = dnfsBySeason[dnfsBySeason.length - 1]
    return {
      seasonsTracked: dnfsBySeason.length,
      currentDnfRate: latestDnf?.dnf_rate_percent ?? 'N/A',
      bestDriver: topDrivers[0] ? `${topDrivers[0].forename} ${topDrivers[0].surname}` : 'N/A',
      bestConstructor: topConstructors[0]?.constructor_name || 'N/A',
    }
  }, [dnfsBySeason, topDrivers, topConstructors])

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <h2>Formula 1 Analytics Hub</h2>
          <p>
            Explore trends, title fights, circuit specialists, teammate battles,
            rivalries, comebacks, and historical constructor performance.
          </p>
        </div>

        <div className="analytics-controls">
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="analytics-select"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>

          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="analytics-select"
          >
            <option value="wins">Wins</option>
            <option value="podiums">Podiums</option>
            <option value="points">Points</option>
          </select>
        </div>
      </div>

      <div className="analytics-tabs">
        <button className={activeTab === 'overview' ? 'analytics-tab active-analytics-tab' : 'analytics-tab'} onClick={() => setActiveTab('overview')}>Overview</button>
        <button className={activeTab === 'rankings' ? 'analytics-tab active-analytics-tab' : 'analytics-tab'} onClick={() => setActiveTab('rankings')}>Rankings</button>
        <button className={activeTab === 'battles' ? 'analytics-tab active-analytics-tab' : 'analytics-tab'} onClick={() => setActiveTab('battles')}>Battles</button>
        <button className={activeTab === 'circuits' ? 'analytics-tab active-analytics-tab' : 'analytics-tab'} onClick={() => setActiveTab('circuits')}>Circuits</button>
        <button className={activeTab === 'history' ? 'analytics-tab active-analytics-tab' : 'analytics-tab'} onClick={() => setActiveTab('history')}>History</button>
      </div>

      {loading && <p className="analytics-message">Loading analytics...</p>}
      {error && <p className="analytics-message error">{error}</p>}

      {!loading && !error && activeTab === 'overview' && (
        <>
          <div className="analytics-stat-grid">
            <div className="analytics-stat-card">
              <span>Seasons Tracked</span>
              <strong>{overviewStats.seasonsTracked}</strong>
            </div>
            <div className="analytics-stat-card">
              <span>Latest DNF Rate</span>
              <strong>{overviewStats.currentDnfRate}%</strong>
            </div>
            <div className="analytics-stat-card">
              <span>Top Driver</span>
              <strong>{overviewStats.bestDriver}</strong>
            </div>
            <div className="analytics-stat-card">
              <span>Top Constructor</span>
              <strong>{overviewStats.bestConstructor}</strong>
            </div>
          </div>

          <div className="analytics-section">
            <h3>DNF Trends by Season</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>Total Results</th>
                    <th>Non-Finishes</th>
                    <th>DNF Rate %</th>
                  </tr>
                </thead>
                <tbody>
                  {dnfsBySeason.map((item) => (
                    <tr key={item.year}>
                      <td>{item.year}</td>
                      <td>{item.total_results}</td>
                      <td>{item.non_finishes}</td>
                      <td>{item.dnf_rate_percent}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="analytics-section">
            <h3>Title Fight Progression — {season}</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Round</th>
                    <th>Position</th>
                    <th>Driver</th>
                    <th>Code</th>
                    <th>Cumulative Points</th>
                  </tr>
                </thead>
                <tbody>
                  {titleFightProgression.map((item, index) => (
                    <tr key={index}>
                      <td>{item.round}</td>
                      <td>{item.standing_position}</td>
                      <td>{item.forename} {item.surname}</td>
                      <td>{item.code || 'N/A'}</td>
                      <td>{item.cumulative_points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !error && activeTab === 'rankings' && (
        <>
          <div className="analytics-section">
            <h3>Most Successful Drivers</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
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
                  {topDrivers.map((driver) => (
                    <tr key={driver.driver_id}>
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

          <div className="analytics-section">
            <h3>Most Successful Constructors</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
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
                  {topConstructors.map((constructor) => (
                    <tr key={constructor.constructor_id}>
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

          <div className="analytics-section">
            <h3>Comeback Drivers</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Driver</th>
                    <th>Code</th>
                    <th>Nationality</th>
                    <th>Avg Positions Gained</th>
                    <th>Best Single Comeback</th>
                    <th>Entries</th>
                  </tr>
                </thead>
                <tbody>
                  {comebackDrivers.map((driver) => (
                    <tr key={driver.driver_id}>
                      <td>{driver.forename} {driver.surname}</td>
                      <td>{driver.code || 'N/A'}</td>
                      <td>{driver.nationality || 'N/A'}</td>
                      <td>{driver.average_positions_gained}</td>
                      <td>{driver.best_single_race_comeback}</td>
                      <td>{driver.race_entries}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !error && activeTab === 'battles' && (
        <>
          <div className="analytics-section">
            <h3>Championship Battles — {season}</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Driver</th>
                    <th>Points</th>
                    <th>Wins</th>
                    <th>Podiums</th>
                    <th>Gap to Leader</th>
                  </tr>
                </thead>
                <tbody>
                  {championshipBattles.map((driver) => (
                    <tr key={driver.driver_id}>
                      <td>{driver.forename} {driver.surname}</td>
                      <td>{driver.total_points}</td>
                      <td>{driver.wins}</td>
                      <td>{driver.podiums}</td>
                      <td>{driver.points_gap_to_leader ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="analytics-section">
            <h3>Closest Title Fights</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>Champion</th>
                    <th>Runner-Up</th>
                    <th>Champion Points</th>
                    <th>Runner-Up Points</th>
                    <th>Gap</th>
                  </tr>
                </thead>
                <tbody>
                  {closestTitleFights.map((fight, index) => (
                    <tr key={index}>
                      <td>{fight.year}</td>
                      <td>{fight.champion_forename} {fight.champion_surname}</td>
                      <td>{fight.runner_up_forename} {fight.runner_up_surname}</td>
                      <td>{fight.champion_points}</td>
                      <td>{fight.runner_up_points}</td>
                      <td>{fight.points_gap}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="analytics-section">
            <h3>Teammate Battles — {season}</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Constructor</th>
                    <th>Driver 1</th>
                    <th>Driver 2</th>
                    <th>Shared Races</th>
                    <th>D1 Points</th>
                    <th>D2 Points</th>
                    <th>D1 Ahead</th>
                    <th>D2 Ahead</th>
                  </tr>
                </thead>
                <tbody>
                  {teammateBattles.map((battle, index) => (
                    <tr key={index}>
                      <td>{battle.constructor_name}</td>
                      <td>{battle.driver_1_forename} {battle.driver_1_surname}</td>
                      <td>{battle.driver_2_forename} {battle.driver_2_surname}</td>
                      <td>{battle.shared_races}</td>
                      <td>{battle.driver_1_points}</td>
                      <td>{battle.driver_2_points}</td>
                      <td>{battle.driver_1_ahead_finishes}</td>
                      <td>{battle.driver_2_ahead_finishes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="analytics-section">
            <h3>Driver Rivalries</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Driver 1</th>
                    <th>Driver 2</th>
                    <th>Shared Races</th>
                    <th>D1 Ahead</th>
                    <th>D2 Ahead</th>
                    <th>D1 Points</th>
                    <th>D2 Points</th>
                    <th>Years</th>
                  </tr>
                </thead>
                <tbody>
                  {driverRivalries.map((rivalry, index) => (
                    <tr key={index}>
                      <td>{rivalry.driver_1_forename} {rivalry.driver_1_surname}</td>
                      <td>{rivalry.driver_2_forename} {rivalry.driver_2_surname}</td>
                      <td>{rivalry.shared_races}</td>
                      <td>{rivalry.driver_1_ahead_finishes}</td>
                      <td>{rivalry.driver_2_ahead_finishes}</td>
                      <td>{rivalry.driver_1_points}</td>
                      <td>{rivalry.driver_2_points}</td>
                      <td>{rivalry.first_shared_year} - {rivalry.last_shared_year}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !error && activeTab === 'circuits' && (
        <>
          <div className="analytics-section">
            <h3>Circuit Specialists</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Driver</th>
                    <th>Circuit</th>
                    <th>Country</th>
                    <th>Wins</th>
                    <th>Podiums</th>
                    <th>Points</th>
                    <th>Entries</th>
                  </tr>
                </thead>
                <tbody>
                  {circuitSpecialists.map((item, index) => (
                    <tr key={index}>
                      <td>{item.forename} {item.surname}</td>
                      <td>{item.circuit_name}</td>
                      <td>{item.country}</td>
                      <td>{item.wins}</td>
                      <td>{item.podiums}</td>
                      <td>{item.total_points}</td>
                      <td>{item.race_entries}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="analytics-section">
            <h3>Circuit Difficulty</h3>
            <div className="analytics-table-wrapper">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Circuit</th>
                    <th>Location</th>
                    <th>Country</th>
                    <th>Races Hosted</th>
                    <th>Non-Finishes</th>
                    <th>DNF Rate %</th>
                    <th>Finisher Rate %</th>
                  </tr>
                </thead>
                <tbody>
                  {circuitDifficulty.map((item) => (
                    <tr key={item.circuit_id}>
                      <td>{item.circuit_name}</td>
                      <td>{item.location}</td>
                      <td>{item.country}</td>
                      <td>{item.races_hosted}</td>
                      <td>{item.non_finishes}</td>
                      <td>{item.dnf_rate_percent}</td>
                      <td>{item.finisher_like_rate_percent}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !error && activeTab === 'history' && (
        <div className="analytics-section">
          <h3>Constructors by Era</h3>
          <div className="analytics-table-wrapper">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Era</th>
                  <th>Constructor</th>
                  <th>Nationality</th>
                  <th>Wins</th>
                  <th>Podiums</th>
                  <th>Points</th>
                  <th>Entries</th>
                  <th>Years in Era</th>
                </tr>
              </thead>
              <tbody>
                {constructorsByEra.map((item, index) => (
                  <tr key={index}>
                    <td>{item.era}</td>
                    <td>{item.constructor_name}</td>
                    <td>{item.nationality || 'N/A'}</td>
                    <td>{item.wins}</td>
                    <td>{item.podiums}</td>
                    <td>{item.total_points}</td>
                    <td>{item.race_entries}</td>
                    <td>{item.first_year_in_era} - {item.last_year_in_era}</td>
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

export default AnalyticsPage