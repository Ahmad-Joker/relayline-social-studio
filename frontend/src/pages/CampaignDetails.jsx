import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import PlatformPostCard from '../components/PlatformPostCard'
import StatusBadge from '../components/StatusBadge'
import { api } from '../services/api'
import { ErrorPanel, PageLoading } from './Dashboard'

export default function CampaignDetails() {
  const { id } = useParams()
  const [campaign, setCampaign] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.campaign(id).then(setCampaign).catch((err) => setError(err.message))
  useEffect(() => { load(); const timer = setInterval(load, 5000); return () => clearInterval(timer) }, [id])

  async function publish() {
    setBusy(true)
    setError('')
    try { setCampaign(await api.publish(id)) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  if (error && !campaign) return <ErrorPanel message={error} />
  if (!campaign) return <PageLoading />
  return (
    <>
      <Link className="back-link" to="/campaigns">← Campaigns</Link>
      <header className="detail-heading">
        <div><span className="eyebrow">Campaign / {campaign.id.slice(0, 8)}</span><h1>{campaign.title}</h1><a href={campaign.article_url} target="_blank" rel="noreferrer">Open source article ↗</a></div>
        <div className="detail-actions"><StatusBadge status={campaign.status} /><button className="button button--acid" onClick={publish} disabled={busy}>{busy ? 'Queued…' : 'Publish now'} <span>↗</span></button></div>
      </header>
      {error && <p className="form-error">{error}</p>}
      <div className="campaign-timeline"><div><span>Scheduled</span><strong>{new Date(campaign.scheduled_at).toLocaleString()}</strong></div><div><span>Created</span><strong>{new Date(campaign.created_at).toLocaleString()}</strong></div><div><span>Delivery truth</span><strong>Signed webhook only</strong></div></div>
      <section className="platform-grid">{campaign.social_posts.map((post) => <PlatformPostCard key={post.id} post={post} title={campaign.title} />)}</section>
    </>
  )
}

