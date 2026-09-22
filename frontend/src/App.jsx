import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import CampaignDetails from './pages/CampaignDetails'
import Campaigns from './pages/Campaigns'
import CreateCampaign from './pages/CreateCampaign'
import Dashboard from './pages/Dashboard'
import { api } from './services/api'

export default function App() {
  const [dashboard, setDashboard] = useState(null)
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const location = useLocation()

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [dashboardData, campaignData] = await Promise.all([api.dashboard(), api.campaigns()])
      setDashboard(dashboardData)
      setCampaigns(campaignData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { if (location.pathname === '/' || location.pathname === '/campaigns') refresh() }, [location.pathname, refresh])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" to="/"><span className="brand-mark">R/</span><span>Relayline<small>Social Studio</small></span></Link>
        <nav><NavLink to="/" end><span>01</span>Dashboard</NavLink><NavLink to="/campaigns"><span>02</span>Campaigns</NavLink><NavLink to="/campaigns/new"><span>03</span>Compose</NavLink></nav>
        <div className="sidebar-foot"><span className="signal-dot" /><div><strong>System online</strong><small>Database is truth</small></div></div>
      </aside>
      <main>
        <div className="topline"><span>Multi-platform publishing console</span><span>{new Date().toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}</span></div>
        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard data={dashboard || { total: 0, scheduled: 0, publishing: 0, published: 0, failed: 0, recent_campaigns: [] }} loading={loading} error={error} />} />
            <Route path="/campaigns" element={<Campaigns campaigns={campaigns} loading={loading} error={error} />} />
            <Route path="/campaigns/new" element={<CreateCampaign />} />
            <Route path="/campaigns/:id" element={<CampaignDetails />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

