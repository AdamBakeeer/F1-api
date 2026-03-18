import { useEffect, useState } from 'react'
import './App.css'
import DriversPage from './pages/DriversPage'
import ConstructorsPage from './pages/ConstructorsPage'
import CircuitsPage from './pages/CircuitsPage'
import RacesPage from './pages/RacesPage'
import AnalyticsPage from './pages/AnalyticsPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import UserPage from './pages/UserPage'
import AdminPage from './pages/AdminPage'

function App() {
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState('home')

  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('currentUser')
    return saved ? JSON.parse(saved) : null
  })

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
  }, [token])

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem('currentUser', JSON.stringify(currentUser))
    } else {
      localStorage.removeItem('currentUser')
    }
  }, [currentUser])

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

  const handleLoginSuccess = ({ token, user }) => {
    setToken(token)
    setCurrentUser(user)

    if (user.role === 'admin') {
      setPage('admin')
    } else {
      setPage('user')
    }
  }

  const handleLogout = () => {
    setToken('')
    setCurrentUser(null)
    setPage('home')
  }

  const isLoggedIn = !!token && !!currentUser
  const isAdmin = currentUser?.role === 'admin'

  return (
    <div className="app">
      <nav className="navbar">
        <h1 onClick={() => setPage('home')} style={{ cursor: 'pointer' }}>
          F1 Data Platform
        </h1>

        <div className="nav-links">
          <button onClick={() => setPage('drivers')}>Drivers</button>
          <button onClick={() => setPage('constructors')}>Constructors</button>
          <button onClick={() => setPage('circuits')}>Circuits</button>
          <button onClick={() => setPage('races')}>Races</button>
          <button onClick={() => setPage('analytics')}>Analytics</button>

          {!isLoggedIn && (
            <>
              <button onClick={() => setPage('login')}>Login</button>
              <button className="login-btn" onClick={() => setPage('signup')}>
                Sign Up
              </button>
            </>
          )}

          {isLoggedIn && !isAdmin && (
            <>
              <button onClick={() => setPage('user')}>My Account</button>
              <button className="login-btn" onClick={handleLogout}>
                Logout
              </button>
            </>
          )}

          {isLoggedIn && isAdmin && (
            <>
              <button onClick={() => setPage('admin')}>Admin</button>
              <button className="login-btn" onClick={handleLogout}>
                Logout
              </button>
            </>
          )}
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

      {page === 'drivers' && (
        <DriversPage
          token={token}
          currentUser={currentUser}
        />
      )}

      {page === 'constructors' && (
        <ConstructorsPage
          token={token}
          currentUser={currentUser}
        />
      )}

      {page === 'circuits' && (
        <CircuitsPage
          token={token}
          currentUser={currentUser}
        />
      )}

      {page === 'races' && <RacesPage />}
      {page === 'analytics' && <AnalyticsPage />}

      {page === 'login' && (
        <LoginPage
          onLoginSuccess={handleLoginSuccess}
          goToSignup={() => setPage('signup')}
          goHome={() => setPage('home')}
        />
      )}

      {page === 'signup' && (
        <SignupPage
          onSignupSuccess={handleLoginSuccess}
          goToLogin={() => setPage('login')}
          goHome={() => setPage('home')}
        />
      )}

      {page === 'user' && (
        <UserPage
          currentUser={currentUser}
          token={token}
          onUserUpdate={setCurrentUser}
          onLogout={handleLogout}
          goHome={() => setPage('home')}
        />
      )}

      {page === 'admin' && (
        <AdminPage
          token={token}
          currentUser={currentUser}
          goHome={() => setPage('home')}
        />
      )}
    </div>
  )
}

export default App