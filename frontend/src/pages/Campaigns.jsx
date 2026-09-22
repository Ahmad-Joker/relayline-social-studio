import { Link } from 'react-router-dom'
import CampaignTable from '../components/CampaignTable'
import { ErrorPanel, PageLoading } from './Dashboard'

export default function Campaigns({ campaigns, loading, error }) {
  return (
    <>
      <header className="page-heading page-heading--compact">
        <div><span className="eyebrow">Archive / durable records</span><h1>Campaigns</h1></div>
        <Link className="button button--acid" to="/campaigns/new">New campaign <span>＋</span></Link>
      </header>
      {loading ? <PageLoading /> : error ? <ErrorPanel message={error} /> : <CampaignTable campaigns={campaigns} />}
    </>
  )
}

