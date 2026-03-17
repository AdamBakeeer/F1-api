import { useState } from 'react'
import './App.css'
import DriversPage from './pages/DriversPage'
import ConstructorsPage from './pages/ConstructorsPage'
import RacesPage from './pages/RacesPage'
import CircuitsPage from './pages/CircuitsPage'

function App() {
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState('home')

  const fetchDrivers = async () => {
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/drivers/current')
      const data = await response.json()
      setDrivers(data.data || [])
    } catch (error) {
      console.error('Error fetching drivers:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <nav className="navbar">
        <h1>F1 Data Platform</h1>

        <div className="nav-links">
          <button onClick={() => setPage('drivers')}>Drivers</button>
          <button onClick={() => setPage('constructors')}>Constructors</button>
          <button onClick={() => setPage('races')}>Races</button>
          <button onClick={() => setPage('circuits')}>Circuits</button>
          <a href="#">Analytics</a>
          <button className="login-btn">Login</button>
        </div>
      </nav>

      {page === 'home' && (
        <>
          <section className="hero">
            <h2>Formula 1 Analytics API</h2>
            <p>
              Explore drivers, constructors, circuits, races and advanced analytics
              powered by your FastAPI backend.
            </p>

            <button className="explore-btn" onClick={fetchDrivers}>
              Explore Data
            </button>
          </section>

          <section className="drivers-section">
            <h3>Current Drivers</h3>

            {loading ? (
              <p className="loading-text">Loading drivers...</p>
            ) : (
              <div className="drivers-grid">
                {drivers.map((driver) => (
                  <div key={driver.driver_id} className="driver-card">
                    <h4>{driver.forename} {driver.surname}</h4>
                    <p><strong>Code:</strong> {driver.code || 'N/A'}</p>
                    <p><strong>Nationality:</strong> {driver.nationality || 'N/A'}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {page === 'drivers' && <DriversPage />}
      {page === 'constructors' && <ConstructorsPage />}
      {page === 'races' && <RacesPage />}
      {page === 'circuits' && <CircuitsPage />}
    </div>
  )
}

export default App

