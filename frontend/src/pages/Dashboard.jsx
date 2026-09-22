import { Link } from 'react-router-dom'
import CampaignTable from '../components/CampaignTable'

const cards = [
  ['total', 'All campaigns'],
  ['scheduled', 'Scheduled'],
  ['publishing', 'In flight'],
  ['published', 'Published'],
  ['failed', 'Failed'],
]

export default function Dashboard({ data, loading, error }) {
  if (loading) return <PageLoading />
  if (error) return <ErrorPanel message={error} />
  return (
    <>
      <header className="page-heading dashboard-heading">
        <div>
          <span className="eyebrow">Operations / live state</span>
          <h1>Keep every post<br /><em>on the line.</em></h1>
        </div>
        <div className="heading-note">
          <span className="pulse" />
          <p>Durable queue active<br /><strong>Webhook-trusted delivery</strong></p>
        </div>
      </header>

      <section className="metric-grid" aria-label="Campaign metrics">
        {cards.map(([key, label], index) => (
          <article className={`metric metric--${key}`} key={key}>
            <span>0{index + 1}</span><strong>{String(data[key]).padStart(2, '0')}</strong><p>{label}</p>
          </article>
        ))}
      </section>

      <section className="section-block">
        <div className="section-title"><div><span className="eyebrow">Recent transmissions</span><h2>Campaign desk</h2></div><Link className="text-link" to="/campaigns">View all →</Link></div>
        <CampaignTable campaigns={data.recent_campaigns} />
      </section>
    </>
  )
}

export function PageLoading() {
  return <div className="loading"><span /><p>Reading durable state…</p></div>
}

export function ErrorPanel({ message }) {
  return <div className="error-panel"><span>Connection fault</span><h2>The studio could not reach the API.</h2><p>{message}</p></div>
}

