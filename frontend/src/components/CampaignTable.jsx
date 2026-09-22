import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge'

export default function CampaignTable({ campaigns }) {
  if (!campaigns?.length) {
    return (
      <div className="empty-state">
        <span>00</span>
        <h3>No campaigns on the wire</h3>
        <p>Create the first one to see durable delivery state here.</p>
        <Link className="text-link" to="/campaigns/new">Create campaign →</Link>
      </div>
    )
  }
  return (
    <div className="table-wrap">
      <table className="campaign-table">
        <thead><tr><th>Campaign</th><th>Instagram</th><th>X</th><th>Scheduled</th><th aria-label="Open" /></tr></thead>
        <tbody>
          {campaigns.map((campaign) => {
            const instagram = campaign.social_posts.find((post) => post.platform === 'instagram')
            const x = campaign.social_posts.find((post) => post.platform === 'x')
            return (
              <tr key={campaign.id}>
                <td><strong>{campaign.title}</strong><small>{campaign.article_url.replace(/^https?:\/\//, '')}</small></td>
                <td>{instagram ? <StatusBadge status={instagram.status} /> : <span className="muted">—</span>}</td>
                <td>{x ? <StatusBadge status={x.status} /> : <span className="muted">—</span>}</td>
                <td className="mono">{new Date(campaign.scheduled_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                <td><Link className="row-arrow" to={`/campaigns/${campaign.id}`} aria-label={`Open ${campaign.title}`}>↗</Link></td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

