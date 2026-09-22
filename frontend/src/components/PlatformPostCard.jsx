import StatusBadge from './StatusBadge'

export default function PlatformPostCard({ post, title }) {
  const isInstagram = post.platform === 'instagram'
  return (
    <article className={`platform-card platform-card--${post.platform}`}>
      <div className="platform-card__head">
        <div>
          <span className="eyebrow">{isInstagram ? 'IG / 01' : 'X / 02'}</span>
          <h3>{isInstagram ? 'Instagram' : 'X'}</h3>
        </div>
        <StatusBadge status={post.status} />
      </div>
      <div className={`post-preview ${isInstagram ? 'post-preview--square' : 'post-preview--wide'}`}>
        <img src={post.image_url} alt={`${title} — ${post.platform} variant`} />
        <span>{isInstagram ? '1080 × 1080' : '1600 × 900'}</span>
      </div>
      <p className="caption">{post.caption}</p>
      <dl className="post-meta">
        <div><dt>Attempts</dt><dd>{post.publish_attempt_count} / {post.max_attempts}</dd></div>
        <div><dt>Idempotency</dt><dd className="mono">{post.idempotency_key.slice(0, 12)}…</dd></div>
        <div><dt>External ID</dt><dd className="mono">{post.external_post_id || 'Pending'}</dd></div>
        <div><dt>Last signal</dt><dd>{post.last_error_safe || (post.status === 'awaiting_delivery' ? 'Awaiting verified webhook' : 'No errors')}</dd></div>
      </dl>
    </article>
  )
}

