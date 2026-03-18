import { useEffect, useState } from 'react'
import { API_BASE_URL } from '../config.js'
import './AdminPage.css'

function AdminPage({ token, currentUser, goHome }) {
  const [driversCount, setDriversCount] = useState(0)
  const [constructorsCount, setConstructorsCount] = useState(0)
  const [circuitsCount, setCircuitsCount] = useState(0)
  const [racesCount, setRacesCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [entityTab, setEntityTab] = useState('drivers')
  const [adminTab, setAdminTab] = useState('create')
  const [adminMessage, setAdminMessage] = useState('')
  const [adminError, setAdminError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const [createDriverForm, setCreateDriverForm] = useState({
    driver_ref: '',
    number: '',
    code: '',
    forename: '',
    surname: '',
    dob: '',
    nationality: ''
  })

  const [updateDriverSlug, setUpdateDriverSlug] = useState('')
  const [updateDriverForm, setUpdateDriverForm] = useState({
    driver_ref: '',
    number: '',
    code: '',
    forename: '',
    surname: '',
    dob: '',
    nationality: ''
  })

  const [deleteDriverSlug, setDeleteDriverSlug] = useState('')

  const [createConstructorForm, setCreateConstructorForm] = useState({
    constructor_ref: '',
    name: '',
    nationality: ''
  })

  const [updateConstructorSlug, setUpdateConstructorSlug] = useState('')
  const [updateConstructorForm, setUpdateConstructorForm] = useState({
    constructor_ref: '',
    name: '',
    nationality: ''
  })

  const [deleteConstructorSlug, setDeleteConstructorSlug] = useState('')

  const [createCircuitForm, setCreateCircuitForm] = useState({
    name: '',
    location: '',
    country: '',
    lat: '',
    lng: '',
    alt: ''
  })

  const [updateCircuitSlug, setUpdateCircuitSlug] = useState('')
  const [updateCircuitForm, setUpdateCircuitForm] = useState({
    name: '',
    location: '',
    country: '',
    lat: '',
    lng: '',
    alt: ''
  })

  const [deleteCircuitSlug, setDeleteCircuitSlug] = useState('')

  useEffect(() => {
    fetchAdminOverview()
  }, [])

  const fetchAdminOverview = async () => {
    try {
      setLoading(true)
      setError('')

      const [
        driversRes,
        constructorsRes,
        circuitsRes,
        racesRes
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/drivers?limit=200`),
        fetch(`${API_BASE_URL}/constructors?limit=200`),
        fetch(`${API_BASE_URL}/circuits?limit=200`),
        fetch(`${API_BASE_URL}/races?limit=200`)
      ])

      const driversData = await driversRes.json()
      const constructorsData = await constructorsRes.json()
      const circuitsData = await circuitsRes.json()
      const racesData = await racesRes.json()

      if (!driversRes.ok) throw new Error(driversData.detail || 'Failed to load drivers')
      if (!constructorsRes.ok) throw new Error(constructorsData.detail || 'Failed to load constructors')
      if (!circuitsRes.ok) throw new Error(circuitsData.detail || 'Failed to load circuits')
      if (!racesRes.ok) throw new Error(racesData.detail || 'Failed to load races')

      setDriversCount(driversData.count || 0)
      setConstructorsCount(constructorsData.count || 0)
      setCircuitsCount(circuitsData.count || 0)
      setRacesCount(racesData.count || 0)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  }

  const resetMessages = () => {
    setAdminMessage('')
    setAdminError('')
  }

  const resetAllForms = () => {
    setCreateDriverForm({
      driver_ref: '',
      number: '',
      code: '',
      forename: '',
      surname: '',
      dob: '',
      nationality: ''
    })
    setUpdateDriverSlug('')
    setUpdateDriverForm({
      driver_ref: '',
      number: '',
      code: '',
      forename: '',
      surname: '',
      dob: '',
      nationality: ''
    })
    setDeleteDriverSlug('')

    setCreateConstructorForm({
      constructor_ref: '',
      name: '',
      nationality: ''
    })
    setUpdateConstructorSlug('')
    setUpdateConstructorForm({
      constructor_ref: '',
      name: '',
      nationality: ''
    })
    setDeleteConstructorSlug('')

    setCreateCircuitForm({
      name: '',
      location: '',
      country: '',
      lat: '',
      lng: '',
      alt: ''
    })
    setUpdateCircuitSlug('')
    setUpdateCircuitForm({
      name: '',
      location: '',
      country: '',
      lat: '',
      lng: '',
      alt: ''
    })
    setDeleteCircuitSlug('')
  }

  const handleCreateDriverChange = (e) => {
    setCreateDriverForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleUpdateDriverChange = (e) => {
    setUpdateDriverForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleCreateConstructorChange = (e) => {
    setCreateConstructorForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleUpdateConstructorChange = (e) => {
    setUpdateConstructorForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleCreateCircuitChange = (e) => {
    setCreateCircuitForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleUpdateCircuitChange = (e) => {
    setUpdateCircuitForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const buildCreateDriverPayload = () => ({
    driver_ref: createDriverForm.driver_ref,
    number: createDriverForm.number === '' ? null : Number(createDriverForm.number),
    code: createDriverForm.code || null,
    forename: createDriverForm.forename,
    surname: createDriverForm.surname,
    dob: createDriverForm.dob,
    nationality: createDriverForm.nationality
  })

  const buildUpdateDriverPayload = () => {
    const payload = {}

    if (updateDriverForm.driver_ref.trim()) payload.driver_ref = updateDriverForm.driver_ref.trim()
    if (updateDriverForm.number !== '') payload.number = Number(updateDriverForm.number)
    if (updateDriverForm.code.trim()) payload.code = updateDriverForm.code.trim()
    if (updateDriverForm.forename.trim()) payload.forename = updateDriverForm.forename.trim()
    if (updateDriverForm.surname.trim()) payload.surname = updateDriverForm.surname.trim()
    if (updateDriverForm.dob) payload.dob = updateDriverForm.dob
    if (updateDriverForm.nationality.trim()) payload.nationality = updateDriverForm.nationality.trim()

    return payload
  }

  const buildCreateConstructorPayload = () => ({
    constructor_ref: createConstructorForm.constructor_ref || null,
    name: createConstructorForm.name,
    nationality: createConstructorForm.nationality
  })

  const buildUpdateConstructorPayload = () => {
    const payload = {}

    if (updateConstructorForm.constructor_ref.trim()) payload.constructor_ref = updateConstructorForm.constructor_ref.trim()
    if (updateConstructorForm.name.trim()) payload.name = updateConstructorForm.name.trim()
    if (updateConstructorForm.nationality.trim()) payload.nationality = updateConstructorForm.nationality.trim()

    return payload
  }

  const buildCreateCircuitPayload = () => ({
    name: createCircuitForm.name,
    location: createCircuitForm.location || null,
    country: createCircuitForm.country || null,
    lat: createCircuitForm.lat === '' ? null : Number(createCircuitForm.lat),
    lng: createCircuitForm.lng === '' ? null : Number(createCircuitForm.lng),
    alt: createCircuitForm.alt === '' ? null : Number(createCircuitForm.alt)
  })

  const buildUpdateCircuitPayload = () => {
    const payload = {}

    if (updateCircuitForm.name.trim()) payload.name = updateCircuitForm.name.trim()
    if (updateCircuitForm.location.trim()) payload.location = updateCircuitForm.location.trim()
    if (updateCircuitForm.country.trim()) payload.country = updateCircuitForm.country.trim()
    if (updateCircuitForm.lat !== '') payload.lat = Number(updateCircuitForm.lat)
    if (updateCircuitForm.lng !== '') payload.lng = Number(updateCircuitForm.lng)
    if (updateCircuitForm.alt !== '') payload.alt = Number(updateCircuitForm.alt)

    return payload
  }

  const handleCreateDriver = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      const response = await fetch(`${API_BASE_URL}/drivers`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(buildCreateDriverPayload())
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to create driver')
      }

      setAdminMessage('Driver created successfully.')
      setCreateDriverForm({
        driver_ref: '',
        number: '',
        code: '',
        forename: '',
        surname: '',
        dob: '',
        nationality: ''
      })
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateDriver = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      const payload = buildUpdateDriverPayload()

      if (!updateDriverSlug.trim()) {
        throw new Error('Please enter a driver slug to update')
      }

      if (Object.keys(payload).length === 0) {
        throw new Error('Please enter at least one field to update')
      }

      const response = await fetch(`${API_BASE_URL}/drivers/${updateDriverSlug.trim()}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to update driver')
      }

      setAdminMessage('Driver updated successfully.')
      setUpdateDriverForm({
        driver_ref: '',
        number: '',
        code: '',
        forename: '',
        surname: '',
        dob: '',
        nationality: ''
      })
      setUpdateDriverSlug('')
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteDriver = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      if (!deleteDriverSlug.trim()) {
        throw new Error('Please enter a driver slug to delete')
      }

      const response = await fetch(`${API_BASE_URL}/drivers/${deleteDriverSlug.trim()}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to delete driver')
      }

      setAdminMessage('Driver deleted successfully.')
      setDeleteDriverSlug('')
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateConstructor = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      const response = await fetch(`${API_BASE_URL}/constructors`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(buildCreateConstructorPayload())
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to create constructor')
      }

      setAdminMessage('Constructor created successfully.')
      setCreateConstructorForm({
        constructor_ref: '',
        name: '',
        nationality: ''
      })
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateConstructor = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      const payload = buildUpdateConstructorPayload()

      if (!updateConstructorSlug.trim()) {
        throw new Error('Please enter a constructor slug to update')
      }

      if (Object.keys(payload).length === 0) {
        throw new Error('Please enter at least one field to update')
      }

      const response = await fetch(`${API_BASE_URL}/constructors/${updateConstructorSlug.trim()}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to update constructor')
      }

      setAdminMessage('Constructor updated successfully.')
      setUpdateConstructorForm({
        constructor_ref: '',
        name: '',
        nationality: ''
      })
      setUpdateConstructorSlug('')
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteConstructor = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      if (!deleteConstructorSlug.trim()) {
        throw new Error('Please enter a constructor slug to delete')
      }

      const response = await fetch(`${API_BASE_URL}/constructors/${deleteConstructorSlug.trim()}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to delete constructor')
      }

      setAdminMessage('Constructor deleted successfully.')
      setDeleteConstructorSlug('')
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateCircuit = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      const response = await fetch(`${API_BASE_URL}/circuits`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(buildCreateCircuitPayload())
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to create circuit')
      }

      setAdminMessage('Circuit created successfully.')
      setCreateCircuitForm({
        name: '',
        location: '',
        country: '',
        lat: '',
        lng: '',
        alt: ''
      })
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdateCircuit = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      const payload = buildUpdateCircuitPayload()

      if (!updateCircuitSlug.trim()) {
        throw new Error('Please enter a circuit slug to update')
      }

      if (Object.keys(payload).length === 0) {
        throw new Error('Please enter at least one field to update')
      }

      const response = await fetch(`${API_BASE_URL}/circuits/${updateCircuitSlug.trim()}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to update circuit')
      }

      setAdminMessage('Circuit updated successfully.')
      setUpdateCircuitForm({
        name: '',
        location: '',
        country: '',
        lat: '',
        lng: '',
        alt: ''
      })
      setUpdateCircuitSlug('')
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteCircuit = async (e) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      resetMessages()

      if (!deleteCircuitSlug.trim()) {
        throw new Error('Please enter a circuit slug to delete')
      }

      const response = await fetch(`${API_BASE_URL}/circuits/${deleteCircuitSlug.trim()}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to delete circuit')
      }

      setAdminMessage('Circuit deleted successfully.')
      setDeleteCircuitSlug('')
      fetchAdminOverview()
    } catch (err) {
      setAdminError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  if (!currentUser || currentUser.role !== 'admin') {
    return (
      <div className="admin-page">
        <div className="admin-card">
          <h2>Access Denied</h2>
          <p>This page is only available to admin users.</p>
          <button className="admin-btn" onClick={goHome}>Back Home</button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>Admin Dashboard</h2>
        <p>Manage and monitor the F1 Data Platform.</p>
      </div>

      <div className="admin-top-card">
        <div className="admin-top-line"></div>
        <h3>Welcome, {currentUser.username}</h3>
        <p><strong>Role:</strong> {currentUser.role}</p>
        <p><strong>Access:</strong> Protected admin functionality</p>
      </div>

      {loading && <p className="admin-message">Loading dashboard...</p>}
      {error && <p className="admin-message error">{error}</p>}

      {!loading && !error && (
        <>
          <div className="admin-stats-grid">
            <div className="admin-stat-box">
              <span>Drivers</span>
              <strong>{driversCount}</strong>
            </div>
            <div className="admin-stat-box">
              <span>Constructors</span>
              <strong>{constructorsCount}</strong>
            </div>
            <div className="admin-stat-box">
              <span>Circuits</span>
              <strong>{circuitsCount}</strong>
            </div>
            <div className="admin-stat-box">
              <span>Races</span>
              <strong>{racesCount}</strong>
            </div>
          </div>

          <div className="admin-sections">
            <div className="admin-panel">
              <h3>Admin Capabilities</h3>
              <ul>
                <li>Create and update drivers</li>
                <li>Create and update constructors</li>
                <li>Create and update circuits</li>
                <li>Create and update races</li>
                <li>Control protected write endpoints</li>
              </ul>
            </div>

            <div className="admin-panel">
              <h3>Submission Note</h3>
              <p>
                This dashboard demonstrates that the system supports an
                authenticated admin role separately from normal users.
              </p>
            </div>
          </div>

          <div className="admin-crud-panel">
            <h3>Manage Data</h3>

            <div className="admin-crud-tabs">
              <button
                className={entityTab === 'drivers' ? 'admin-btn' : 'admin-btn secondary-admin-btn'}
                onClick={() => {
                  setEntityTab('drivers')
                  setAdminTab('create')
                  resetMessages()
                  resetAllForms()
                }}
                type="button"
              >
                Drivers
              </button>
              <button
                className={entityTab === 'constructors' ? 'admin-btn' : 'admin-btn secondary-admin-btn'}
                onClick={() => {
                  setEntityTab('constructors')
                  setAdminTab('create')
                  resetMessages()
                  resetAllForms()
                }}
                type="button"
              >
                Constructors
              </button>
              <button
                className={entityTab === 'circuits' ? 'admin-btn' : 'admin-btn secondary-admin-btn'}
                onClick={() => {
                  setEntityTab('circuits')
                  setAdminTab('create')
                  resetMessages()
                  resetAllForms()
                }}
                type="button"
              >
                Circuits
              </button>
            </div>

            <div className="admin-crud-tabs">
              <button
                className={adminTab === 'create' ? 'admin-btn' : 'admin-btn secondary-admin-btn'}
                onClick={() => {
                  setAdminTab('create')
                  resetMessages()
                }}
                type="button"
              >
                Create
              </button>
              <button
                className={adminTab === 'update' ? 'admin-btn' : 'admin-btn secondary-admin-btn'}
                onClick={() => {
                  setAdminTab('update')
                  resetMessages()
                }}
                type="button"
              >
                Update
              </button>
              <button
                className={adminTab === 'delete' ? 'admin-btn' : 'admin-btn secondary-admin-btn'}
                onClick={() => {
                  setAdminTab('delete')
                  resetMessages()
                }}
                type="button"
              >
                Delete
              </button>
            </div>

            {adminMessage && <p className="admin-message success">{adminMessage}</p>}
            {adminError && <p className="admin-message error">{adminError}</p>}

            {entityTab === 'drivers' && adminTab === 'create' && (
              <form className="admin-form-grid" onSubmit={handleCreateDriver}>
                <input
                  name="driver_ref"
                  placeholder="Driver Ref"
                  value={createDriverForm.driver_ref}
                  onChange={handleCreateDriverChange}
                  required
                />
                <input
                  name="number"
                  placeholder="Number"
                  value={createDriverForm.number}
                  onChange={handleCreateDriverChange}
                />
                <input
                  name="code"
                  placeholder="Code"
                  value={createDriverForm.code}
                  onChange={handleCreateDriverChange}
                />
                <input
                  name="forename"
                  placeholder="Forename"
                  value={createDriverForm.forename}
                  onChange={handleCreateDriverChange}
                  required
                />
                <input
                  name="surname"
                  placeholder="Surname"
                  value={createDriverForm.surname}
                  onChange={handleCreateDriverChange}
                  required
                />
                <input
                  name="dob"
                  type="date"
                  value={createDriverForm.dob}
                  onChange={handleCreateDriverChange}
                  required
                />
                <input
                  name="nationality"
                  placeholder="Nationality"
                  value={createDriverForm.nationality}
                  onChange={handleCreateDriverChange}
                  required
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Creating...' : 'Create Driver'}
                </button>
              </form>
            )}

            {entityTab === 'drivers' && adminTab === 'update' && (
              <form className="admin-form-grid" onSubmit={handleUpdateDriver}>
                <input
                  placeholder="Driver slug to update"
                  value={updateDriverSlug}
                  onChange={(e) => setUpdateDriverSlug(e.target.value)}
                  required
                />
                <input
                  name="driver_ref"
                  placeholder="New Driver Ref"
                  value={updateDriverForm.driver_ref}
                  onChange={handleUpdateDriverChange}
                />
                <input
                  name="number"
                  placeholder="New Number"
                  value={updateDriverForm.number}
                  onChange={handleUpdateDriverChange}
                />
                <input
                  name="code"
                  placeholder="New Code"
                  value={updateDriverForm.code}
                  onChange={handleUpdateDriverChange}
                />
                <input
                  name="forename"
                  placeholder="New Forename"
                  value={updateDriverForm.forename}
                  onChange={handleUpdateDriverChange}
                />
                <input
                  name="surname"
                  placeholder="New Surname"
                  value={updateDriverForm.surname}
                  onChange={handleUpdateDriverChange}
                />
                <input
                  name="dob"
                  type="date"
                  value={updateDriverForm.dob}
                  onChange={handleUpdateDriverChange}
                />
                <input
                  name="nationality"
                  placeholder="New Nationality"
                  value={updateDriverForm.nationality}
                  onChange={handleUpdateDriverChange}
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Updating...' : 'Update Driver'}
                </button>
              </form>
            )}

            {entityTab === 'drivers' && adminTab === 'delete' && (
              <form className="admin-form-grid" onSubmit={handleDeleteDriver}>
                <input
                  placeholder="Driver slug to delete"
                  value={deleteDriverSlug}
                  onChange={(e) => setDeleteDriverSlug(e.target.value)}
                  required
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Deleting...' : 'Delete Driver'}
                </button>
              </form>
            )}

            {entityTab === 'constructors' && adminTab === 'create' && (
              <form className="admin-form-grid" onSubmit={handleCreateConstructor}>
                <input
                  name="constructor_ref"
                  placeholder="Constructor Ref"
                  value={createConstructorForm.constructor_ref}
                  onChange={handleCreateConstructorChange}
                />
                <input
                  name="name"
                  placeholder="Constructor Name"
                  value={createConstructorForm.name}
                  onChange={handleCreateConstructorChange}
                  required
                />
                <input
                  name="nationality"
                  placeholder="Nationality"
                  value={createConstructorForm.nationality}
                  onChange={handleCreateConstructorChange}
                  required
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Creating...' : 'Create Constructor'}
                </button>
              </form>
            )}

            {entityTab === 'constructors' && adminTab === 'update' && (
              <form className="admin-form-grid" onSubmit={handleUpdateConstructor}>
                <input
                  placeholder="Constructor slug to update"
                  value={updateConstructorSlug}
                  onChange={(e) => setUpdateConstructorSlug(e.target.value)}
                  required
                />
                <input
                  name="constructor_ref"
                  placeholder="New Constructor Ref"
                  value={updateConstructorForm.constructor_ref}
                  onChange={handleUpdateConstructorChange}
                />
                <input
                  name="name"
                  placeholder="New Name"
                  value={updateConstructorForm.name}
                  onChange={handleUpdateConstructorChange}
                />
                <input
                  name="nationality"
                  placeholder="New Nationality"
                  value={updateConstructorForm.nationality}
                  onChange={handleUpdateConstructorChange}
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Updating...' : 'Update Constructor'}
                </button>
              </form>
            )}

            {entityTab === 'constructors' && adminTab === 'delete' && (
              <form className="admin-form-grid" onSubmit={handleDeleteConstructor}>
                <input
                  placeholder="Constructor slug to delete"
                  value={deleteConstructorSlug}
                  onChange={(e) => setDeleteConstructorSlug(e.target.value)}
                  required
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Deleting...' : 'Delete Constructor'}
                </button>
              </form>
            )}

            {entityTab === 'circuits' && adminTab === 'create' && (
              <form className="admin-form-grid" onSubmit={handleCreateCircuit}>
                <input
                  name="name"
                  placeholder="Circuit Name"
                  value={createCircuitForm.name}
                  onChange={handleCreateCircuitChange}
                  required
                />
                <input
                  name="location"
                  placeholder="Location"
                  value={createCircuitForm.location}
                  onChange={handleCreateCircuitChange}
                />
                <input
                  name="country"
                  placeholder="Country"
                  value={createCircuitForm.country}
                  onChange={handleCreateCircuitChange}
                />
                <input
                  name="lat"
                  placeholder="Latitude"
                  value={createCircuitForm.lat}
                  onChange={handleCreateCircuitChange}
                />
                <input
                  name="lng"
                  placeholder="Longitude"
                  value={createCircuitForm.lng}
                  onChange={handleCreateCircuitChange}
                />
                <input
                  name="alt"
                  placeholder="Altitude"
                  value={createCircuitForm.alt}
                  onChange={handleCreateCircuitChange}
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Creating...' : 'Create Circuit'}
                </button>
              </form>
            )}

            {entityTab === 'circuits' && adminTab === 'update' && (
              <form className="admin-form-grid" onSubmit={handleUpdateCircuit}>
                <input
                  placeholder="Circuit slug to update"
                  value={updateCircuitSlug}
                  onChange={(e) => setUpdateCircuitSlug(e.target.value)}
                  required
                />
                <input
                  name="name"
                  placeholder="New Name"
                  value={updateCircuitForm.name}
                  onChange={handleUpdateCircuitChange}
                />
                <input
                  name="location"
                  placeholder="New Location"
                  value={updateCircuitForm.location}
                  onChange={handleUpdateCircuitChange}
                />
                <input
                  name="country"
                  placeholder="New Country"
                  value={updateCircuitForm.country}
                  onChange={handleUpdateCircuitChange}
                />
                <input
                  name="lat"
                  placeholder="New Latitude"
                  value={updateCircuitForm.lat}
                  onChange={handleUpdateCircuitChange}
                />
                <input
                  name="lng"
                  placeholder="New Longitude"
                  value={updateCircuitForm.lng}
                  onChange={handleUpdateCircuitChange}
                />
                <input
                  name="alt"
                  placeholder="New Altitude"
                  value={updateCircuitForm.alt}
                  onChange={handleUpdateCircuitChange}
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Updating...' : 'Update Circuit'}
                </button>
              </form>
            )}

            {entityTab === 'circuits' && adminTab === 'delete' && (
              <form className="admin-form-grid" onSubmit={handleDeleteCircuit}>
                <input
                  placeholder="Circuit slug to delete"
                  value={deleteCircuitSlug}
                  onChange={(e) => setDeleteCircuitSlug(e.target.value)}
                  required
                />
                <button className="admin-btn" type="submit" disabled={submitting}>
                  {submitting ? 'Deleting...' : 'Delete Circuit'}
                </button>
              </form>
            )}
          </div>

          <div className="admin-actions">
            <button className="admin-btn" onClick={goHome}>Back Home</button>
            <button className="admin-btn secondary-admin-btn" onClick={fetchAdminOverview}>
              Refresh Overview
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default AdminPage