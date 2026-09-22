const API_URL = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const payload = await response.json()
      message = typeof payload.detail === 'string' ? payload.detail : message
    } catch {
      // Preserve the status-based fallback.
    }
    throw new Error(message)
  }
  const payload = await response.json()
  const normalizeCampaign = (campaign) => ({
    ...campaign,
    social_posts: campaign.social_posts?.map((post) => ({
      ...post,
      image_url: post.image_url?.startsWith('/')
        ? `${API_URL === '/api' ? '' : API_URL}${post.image_url}`
        : post.image_url,
    })),
  })
  if (Array.isArray(payload)) return payload.map(normalizeCampaign)
  if (payload?.recent_campaigns) return { ...payload, recent_campaigns: payload.recent_campaigns.map(normalizeCampaign) }
  if (payload?.social_posts) return normalizeCampaign(payload)
  return payload
}

export const api = {
  dashboard: () => request('/dashboard'),
  campaigns: () => request('/campaigns'),
  campaign: (id) => request(`/campaigns/${id}`),
  publish: (id) => request(`/campaigns/${id}/publish`, { method: 'POST' }),
  async createBlog({ title, body, url, image }) {
    const form = new FormData()
    form.append('title', title)
    form.append('body', body)
    form.append('url', url)
    form.append('image', image)
    return request('/blog-posts', { method: 'POST', body: form })
  },
  createCampaign: (payload) => request('/campaigns', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }),
}
