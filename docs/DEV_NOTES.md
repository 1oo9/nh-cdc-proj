# Dev notes

Internal notes for **1oo9** and any later dev. Not for NH.

1oo9 flags the agent when something should be added here. Do not treat this file as a dump.

---

## Locked (2026-08-30)

- Client name in this project: **NH** / `nh`.
- NH-facing documents: French.
- Chair: **1oo9** (only human dev for now).
- Stack lean: Next.js + TS + Tailwind / FastAPI + Pydantic v2 / PostgreSQL / Redis+WS.
- Payments (Stripe): later. `payments` table may exist empty.
- Diner PII: do not store. GDPR respected.
- QR: opaque `public_token`, not table number in the URL.
- Money: integer cents.
- Tenant: `restaurant_id` on every business row from day one.
- Target: MVP in **1–2 weeks**, one real restaurant, before 2026-09-14.

---

## Log

| Date | Note |
|---|---|
| 2026-08-30 | CDC v0.1 structured. Technical answers drafted for NH. PDF export toolchain added. |
