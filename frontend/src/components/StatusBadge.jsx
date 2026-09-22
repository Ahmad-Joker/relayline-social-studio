const labels = {
  queued: 'Scheduled',
  publishing: 'Publishing',
  partially_published: 'Partially published',
  retry_scheduled: 'Rate limited · retry scheduled',
  awaiting_delivery: 'Awaiting delivery',
  published: 'Published',
  failed: 'Failed',
}

export default function StatusBadge({ status }) {
  return <span className={`status status--${status}`}>{labels[status] || status}</span>
}

