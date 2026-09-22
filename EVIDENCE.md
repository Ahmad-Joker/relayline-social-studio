# Verification evidence

This file contains only command output from work actually run in this repository.

## Environment — 2026-09-22

```text
Python 3.13.0
node v24.14.0
npm 11.9.0
Docker version 29.6.2, build dfc4efb
Docker Compose version v5.3.1
git version 2.54.0.windows.1
```

## Supplied dependency inspection

The attachment directory contained one file, `pasted-text.txt` (49,636 bytes). The project workspace contained only `.git`. A search of common local project locations did not locate `challenge-5-social` or a fake social-platform server. End-to-end fake-platform claims remain blocked until that supplied dependency is available.

## Backend verification — 2026-09-22

Command: `cd backend && ..\\.venv\\Scripts\\python -m pytest -q`

```text
.................                                                        [100%]
17 passed in 17.85s
```

The passing suite includes exact 1080×1080 and 1600×900 image assertions, platform caption divergence, AES-GCM round trips and fresh nonces, database ciphertext inspection, stable-key timeout retry, 429 delay and eventual retry, expired-lease recovery, forged/modified webhook rejection, signed webhook acceptance, replay deduplication, database uniqueness, and a clean Alembic upgrade.

Manual migration/import check:

```text
INFO  [alembic.runtime.migration] Running upgrade  -> 20260922_0001, initial durable campaign schema
Relayline Social Studio 20
```

## Frontend and live API path — 2026-09-22

Production build:

```text
vite v8.3.0 building client environment for production...
✓ 32 modules transformed.
dist/index.html                   0.55 kB │ gzip:  0.34 kB
dist/assets/index-DpFbqIk0.css   13.26 kB │ gzip:  3.59 kB
dist/assets/index-LFrguqj1.js   273.48 kB │ gzip: 86.19 kB
✓ built in 1.54s
```

Browser verification used the live React app at `127.0.0.1:5173`, the live FastAPI app at `127.0.0.1:8000`, and a migrated SQLite demo database. The browser created campaign `8cf8f520-5906-418a-9a68-c799d7de0c36` through the real upload form. DOM image inspection returned:

```json
[
  {"naturalWidth":1080,"naturalHeight":1080,"complete":true},
  {"naturalWidth":1600,"naturalHeight":900,"complete":true}
]
```

The campaign detail showed distinct Instagram/X captions, separate stable idempotency prefixes, the signed-webhook trust label, attempt counters, and non-sensitive retry state. Two consecutive manual-publish actions completed after the datetime regression fix without creating additional logical rows.
