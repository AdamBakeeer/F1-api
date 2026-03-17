import { useEffect, useMemo, useState } from 'react'
import './RacesPage.css'
import RaceDetailsPage from './RaceDetailsPage'

function RacesPage() {
  const [calendar, setCalendar] = useState([])
  const [winners, setWinners] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [view, setView] = useState('calendar') // calendar | winners
  const [season, setSeason] = useState('2024')
  const [selectedRace, setSelectedRace] = useState(null)

  const years = useMemo(() => {
    const list = []
    for (let y = 2024; y >= 1950; y--) list.push(y)
    return list
  }, [])

  useEffect(() => {
    fetchData()
  }, [view, season])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')

      const url =
        view === 'calendar'
          ? `http://127.0.0.1:8000/races/season/${season}/calendar`
          : `http://127.0.0.1:8000/races/season/${season}/winners`

      const response = await fetch(url)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch race data')
      }

      if (view === 'calendar') {
        setCalendar(data.data || [])
        setWinners([])
      } else {
        setWinners(data.data || [])
        setCalendar([])
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  if (selectedRace) {
    return (
      <RaceDetailsPage
        year={selectedRace.year}
        round={selectedRace.round}
        goBack={() => setSelectedRace(null)}
      />
    )
  }

  return (
    <div className="races-page">
      <div className="races-header">
        <h2>{view === 'calendar' ? `Race Calendar - ${season}` : `Race Winners - ${season}`}</h2>
        <p>
          Explore Formula 1 race weekends through season schedules, winning records, and detailed event breakdowns.
        </p>
      </div>

      <div className="races-controls">
        <div className="races-tabs">
          <button
            className={view === 'calendar' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('calendar')}
          >
            Calendar
          </button>

          <button
            className={view === 'winners' ? 'tab-btn active-tab' : 'tab-btn'}
            onClick={() => setView('winners')}
          >
            Winners
          </button>
        </div>

        <div className="races-filters">
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

      {loading && <p className="races-message">Loading race data...</p>}
      {error && <p className="races-message error">{error}</p>}

      {!loading && !error && view === 'calendar' && (
        <div className="races-table-wrapper">
          <table className="races-table">
            <thead>
              <tr>
                <th>Round</th>
                <th>Race</th>
                <th>Date</th>
                <th>Circuit</th>
                <th>Location</th>
              </tr>
            </thead>
            <tbody>
              {calendar.map((race) => (
                <tr
                  key={race.race_id}
                  className="races-row"
                  onClick={() => setSelectedRace({ year: Number(season), round: race.round })}
                >
                  <td>{race.round}</td>
                  <td>{race.race_name}</td>
                  <td>{race.date}</td>
                  <td>{race.circuit_name}</td>
                  <td>{race.location}, {race.country}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && view === 'winners' && (
        <div className="races-table-wrapper">
          <table className="races-table">
            <thead>
              <tr>
                <th>Round</th>
                <th>Race</th>
                <th>Date</th>
                <th>Winner</th>
                <th>Code</th>
                <th>Constructor</th>
              </tr>
            </thead>
            <tbody>
              {winners.map((race) => (
                <tr
                  key={race.race_id}
                  className="races-row"
                  onClick={() => setSelectedRace({ year: Number(season), round: race.round })}
                >
                  <td>{race.round}</td>
                  <td>{race.race_name}</td>
                  <td>{race.date}</td>
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
  )
}

export default RacesPage