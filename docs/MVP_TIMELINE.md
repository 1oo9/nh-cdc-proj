# MVP timeline — testable build before 14 September

| | |
|---|---|
| **For** | 1oo9 + Kami |
| **Locked** | 2026-09-03 — NH green light on the technical proposition |
| **Start** | Thu 3 Sep 2026, tonight |
| **Hard gate** | Sun 13 Sep — full parcours testable |
| **Not a work day** | Mon 14 Sep — classes |

Assume **weeknights ~3.5–4 h** (target 20:00–00:00, shift if needed) and **weekend days ~6–8 h**. One human (1oo9), Kami pairing. Green light still required before every push.

**Session close:** French synthèse in `docs/syntheses/` + PDF via `scripts/export_pdf.py` for 1oo9 to send NH. No session is closed without it.

**TDD:** every session is red → green → refactor. A gate is not met because the screen works; it is met when the tests that name that behaviour are green. Do not skip the cycle to go faster.

**Fully testable** means: paper QR (or `/t/<token>`) → menu → options → panier → validation → confirmation → kitchen ticket → statuts through `terminée`, on a phone and a tablet, against real Postgres. No Stripe. No diner PII.

If a session slips, steal from polish (S8–S9), never from S4 (order) or S6 (live kitchen).

---

## Calendar

| # | When | Theme | Done when |
|---|---|---|---|
| **S0** | **Thu 3 Sep — tonight** | Skeleton | `docker compose up` → API `/health` + Next loads |
| **S1** | Fri 4 Sep | Schema + seed | migrate + seed; Chicken Street rows in Postgres |
| **S2** | Sat 5 Sep (long) | Admin menu CRUD | you can build a full menu in admin |
| **S3** | Sun 6 Sep (long) | Tables, QR, client read | phone opens `/t/<token>` and sees the menu |
| **S4** | Mon 7 Sep | Panier + commande | submit creates a DB order + confirmation screen |
| **S5** | Tue 8 Sep | Cuisine (refresh OK) | kitchen shows that order with table + lines |
| **S6** | Wed 9 Sep | Temps réel | new order appears without a refresh (+ poll fallback) |
| **S7** | Thu 10 Sep | Ugly cases + layout | happy path + four failure cases stay clean on phone/tablet |
| **S8** | Fri 11 Sep | Demo data + QR sheet | printable QRs for a handful of tables |
| **S9** | Sat 12 Sep | Second device | phone and tablet hit the **same** running stack |
| **S10** | **Sun 13 Sep — GATE** | Recette | 1oo9 walks NH’s parcours end-to-end; bugs only |

Mon 14 Sep: emergency fixes only. Do not plan features.

---

## S0 — tonight (Thu 3 Sep)

**Goal:** something that boots. No product UI yet.

- Monorepo: `apps/api` (FastAPI), `apps/web` (Next.js + TS + Tailwind), `docker-compose.yml` (Postgres + Redis + api + web).
- Test runners from minute one: **pytest** (API), **Vitest** (web). First failing test: `/health` returns ok — then implement it.
- Env samples, `/health`, empty Next app.
- `.gitignore` for `.venv`, `node_modules`, `.next`.

**Out:** no models, no pages beyond a stub.

**Cut if late:** Redis can wait until S6 **only if** compose already has a Redis service defined. Do not skip Postgres.

---

## S1 — Fri 4 Sep

**Goal:** the data model we promised.

- SQLAlchemy 2 models + Alembic.
- Tables: restaurants, admin_users, tables, categories, products, option_groups, options, orders, order_items, order_item_options, payments (empty).
- Seed: one restaurant, one admin, ~2 categories, a few products, one table token.

**Out:** admin UI, QR files.

---

## S2 — Sat 5 Sep (long)

**Goal:** we operate the menu (NH’s “we edit for the restaurant”).

- Admin login (JWT).
- CRUD: restaurant, categories, products, options, availability, sort order.
- Photos: **URL or local disk** this week. Object storage only if S8 is empty.

**Out:** pretty admin. Forms that work beat a design system.

---

## S3 — Sun 6 Sep (long)

**Goal:** the QR story and a readable menu.

- Table CRUD + `public_token` + QR PNG download.
- Public `GET` menu by token (no auth).
- Next: `/t/[token]` — catégories, produits, photos, prix, options. **Read only.**

**Out:** cart. If Sunday overruns, cart moves to S4 (that is S4’s job).

---

## S4 — Mon 7 Sep

**Goal:** a real order.

- Cart in `sessionStorage` (not the server).
- Personnalisation → panier → valider.
- `POST /orders`: token only (never table number), price snapshot, availability check, idempotency key, per-restaurant `#`.
- Confirmation page. No email, no PII fields.

**This is the first “it is a product” night. Protect it.**

---

## S5 — Tue 8 Sep

**Goal:** cuisine can work even if WS is not ready.

- Kitchen screen: `#`, table label, lines, options, total, status buttons.
- Shared kitchen secret / PIN for the tablet (not a restaurateur account).
- Poll or manual refresh is acceptable **tonight**.

---

## S6 — Wed 9 Sep

**Goal:** the promise “sans rafraîchir”.

- FastAPI WS scoped to `restaurant_id`.
- Redis pub/sub.
- Client kitchen reconnect + 4–5 s poll fallback.

**Out:** fancy animations. A new row appearing is enough.

---

## S7 — Thu 10 Sep

**Goal:** it does not die in a real service.

Must pass:

1. Double tap on Valider → one order.
2. Unknown / rotated token → no menu.
3. Product set unavailable with it still in a cart → reject at submit.
4. Two status clicks on the same ticket → one coherent status.

Phone pass on client, tablet-width pass on kitchen.

---

## S8 — Fri 11 Sep

**Goal:** a demo NH can recognise.

- Seed closer to “Chicken Street Paris”.
- QR sheet for tables (e.g. 12–14).
- French copy on the three surfaces.

**Cut:** photo pipeline polish, extra admin niceties.

---

## S9 — Sat 12 Sep

**Goal:** two devices, one stack.

- Prefer: compose on 1oo9’s machine, phone + tablet on the same LAN.
- Cloud (Fly / Railway) only if LAN is already green and there is time.
- Short runbook in the README (how to boot, seed, find a token).

---

## S10 — Sun 13 Sep — GATE

1oo9, not Kami, clicks the path:

`QR → menu → catégorie → produit → options → panier → validation → confirmation → cuisine (nouvelle → … → terminée)`

Bugfix only. If it passes, the promised deadline is met. Install-in-a-real-restaurant is **after** this gate, not instead of it.

---

## Cut list (if behind)

| Drop first | Keep |
|---|---|
| S3/object storage | local photo URLs |
| Cloud deploy | LAN `docker compose` |
| Admin aesthetics | working CRUD |
| Extra restaurants in seed | one restaurant |
| Kitchen animations | WS + poll |
| Printed sticker run | on-screen QR + PDF sheet |

Do **not** cut: opaque tokens, cents, `restaurant_id`, no diner PII, order snapshot, kitchen statuses.

---

## Tonight, first commands (when you say start)

1. Compose file + Postgres + Redis.
2. FastAPI app with `/health`.
3. Next.js app that fetches that health.
4. Stop. Push only with green light.
