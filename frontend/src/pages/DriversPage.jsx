import { useEffect, useState } from 'react'
import './DriversPage.css'

function DriversPage() {
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDrivers()
  }, [])

  const fetchDrivers = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await fetch('http://127.0.0.1:8000/drivers/current')
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch drivers')
      }

      setDrivers(data.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="drivers-page">
      <div className="drivers-header">
        <h2>Current Drivers</h2>
        <p>Explore the active Formula 1 drivers from your backend API.</p>
      </div>

      {loading && <p className="drivers-message">Loading drivers...</p>}
      {error && <p className="drivers-message error">{error}</p>}

      {!loading && !error && (
        <div className="drivers-grid">
          {drivers.map((driver) => (
            <div key={driver.driver_id} className="driver-card">
              <div className="driver-top-line"></div>
              <h3>
                {driver.forename} {driver.surname}
              </h3>
              <p><strong>Code:</strong> {driver.code || 'N/A'}</p>
              <p><strong>Nationality:</strong> {driver.nationality || 'N/A'}</p>
              <p><strong>Date of Birth:</strong> {driver.dob || 'N/A'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DriversPage