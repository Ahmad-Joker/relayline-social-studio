# Relayline Social Studio

Relayline turns one blog post into a durable Instagram-and-X campaign. It creates platform-specific captions and exact-size image assets, stores scheduled work in PostgreSQL, publishes through adapters, and trusts only signed delivery webhooks for final delivery state.

> The supplied FlyRank fake social-platform server is required for an end-to-end demo. It was not present in the supplied workspace when this repository was initialized. The application integration is intentionally configurable; no replacement server is represented as the supplied dependency.

## Status

Implementation is in progress. See [BUILDLOG.md](BUILDLOG.md) for verified work and [EVIDENCE.md](EVIDENCE.md) for command output.

## Core boundaries

- Core platforms: Instagram and X only.
- Final `PUBLISHED` state comes only from a verified delivery webhook.
- Real social accounts and real social APIs are explicitly out of scope.
- Template captions keep tests and demos deterministic and key-free.

## Planned local endpoints

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

Full setup and acceptance-probe instructions will be completed after implementation and verification.

