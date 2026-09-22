import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'

const initial = { title: '', url: '', body: '', mode: 'now', scheduledAt: '', instagram: true, x: true }

export default function CreateCampaign() {
  const [form, setForm] = useState(initial)
  const [image, setImage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const preview = useMemo(() => image ? URL.createObjectURL(image) : '', [image])

  const update = (event) => {
    const { name, value, checked, type } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    if (!image) return setError('Choose a JPEG, PNG, or WebP source image.')
    const platforms = [form.instagram && 'instagram', form.x && 'x'].filter(Boolean)
    if (!platforms.length) return setError('Select at least one platform.')
    setBusy(true)
    try {
      const blog = await api.createBlog({ ...form, image })
      const scheduledAt = form.mode === 'now' ? new Date().toISOString() : new Date(form.scheduledAt).toISOString()
      const campaign = await api.createCampaign({ blog_post_id: blog.id, platforms, scheduled_at: scheduledAt })
      navigate(`/campaigns/${campaign.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <header className="page-heading page-heading--compact"><div><span className="eyebrow">Compose / one source, two signals</span><h1>New campaign</h1></div><p className="lede">The studio will crop real assets, compose distinct captions, and persist each scheduled delivery.</p></header>
      <form className="create-grid" onSubmit={submit}>
        <section className="editor-panel">
          <div className="field"><label htmlFor="title">Article title</label><input id="title" name="title" value={form.title} onChange={update} minLength="1" maxLength="240" required placeholder="The shape of reliable delivery" /></div>
          <div className="field"><label htmlFor="url">Canonical URL</label><input id="url" name="url" type="url" value={form.url} onChange={update} required placeholder="https://example.com/article" /></div>
          <div className="field"><label htmlFor="body">Article body</label><textarea id="body" name="body" value={form.body} onChange={update} minLength="20" required rows="8" placeholder="Paste the source content. The deterministic composer will extract a focused summary…" /><span className="field-count">{form.body.length.toLocaleString()} chars</span></div>
          <fieldset><legend>Platforms</legend><label className="check"><input type="checkbox" name="instagram" checked={form.instagram} onChange={update} /><span>Instagram</span><small>1080 × 1080</small></label><label className="check"><input type="checkbox" name="x" checked={form.x} onChange={update} /><span>X</span><small>1600 × 900</small></label></fieldset>
          <fieldset><legend>Dispatch</legend><div className="segmented"><label><input type="radio" name="mode" value="now" checked={form.mode === 'now'} onChange={update} /><span>Publish now</span></label><label><input type="radio" name="mode" value="later" checked={form.mode === 'later'} onChange={update} /><span>Schedule</span></label></div>{form.mode === 'later' && <input aria-label="Schedule date and time" type="datetime-local" name="scheduledAt" value={form.scheduledAt} onChange={update} required />}</fieldset>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button--dark button--wide" disabled={busy}>{busy ? 'Building durable campaign…' : 'Create campaign'} <span>↗</span></button>
        </section>
        <aside className="image-drop">
          <span className="eyebrow">Source frame</span>
          <label className={preview ? 'upload-zone has-image' : 'upload-zone'}>
            {preview ? <img src={preview} alt="Selected source preview" /> : <><strong>Drop the lead image</strong><p>JPEG, PNG, or WebP · up to 10 MB</p><span>Choose file</span></>}
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setImage(event.target.files[0] || null)} />
          </label>
          <div className="crop-note"><span>Crop logic</span><p>Center-weighted cover crops keep the primary subject in a safe central zone.</p></div>
        </aside>
      </form>
    </>
  )
}

