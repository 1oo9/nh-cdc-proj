# Dev notes

Internal notes for **1oo9** and any later dev. Not for NH.

**Standing rule (1oo9, 2026-09-06):** when Kami (or any agent) proposes a useful operational note to 1oo9, **also write it here**. Still not a dump — only notes that help run or debug the project.

---

## Locked

- Client: **NH** / `nh`. NH-facing docs: French.
- Chair: **1oo9**. Founding mentor seat: **Kami**.
- Stack: Next.js + TS + Tailwind / FastAPI + Pydantic v2 / PostgreSQL / Redis+WS.
- Payments (Stripe): later. `payments` table exists empty.
- No diner PII. Money: integer cents. Tenant: `restaurant_id` on business rows.
- QR: opaque `public_token`, never `/table/14`.
- TDD mandatory. Session close → French synthèse PDF in `docs/syntheses/` + `docs/pdf/`.
- Hard gate: **2026-09-13** full parcours testable. 14 Sep = classes.

---

## Local toolchain

- **Docker Desktop** is installed; Compose is the normal way to run db/redis/api/web.
- From repo root: `docker compose up --build -d` / `docker compose down` (keep volume; avoid `-v` unless wiping data on purpose).
- Host ports: API `8000`, web `3000`, Postgres `5432`, Redis `6379`. Stop host uvicorn/Next before Compose if ports clash.
- **Node** may live in `.tools/node-env` (conda-forge) if Homebrew Node failed — gitignored. Put it on `PATH` for `npm`.
- Docs PDF: project `.venv` + `scripts/export_pdf.py` (markdown-pdf). Output under `docs/pdf/` (gitignored).

---

## Databases

- App DB: `nh` (`DATABASE_URL=postgresql+asyncpg://nh:nh@localhost:5432/nh`).
- **Test DB: `nh_test`** (`TEST_DATABASE_URL=…/nh_test`). Pytest must never `drop_all` on `nh` — that wiped the demo once (S2). Create once: `CREATE DATABASE nh_test;` as user `nh`.
- After schema work: `cd apps/api && alembic upgrade head && python -m app.seed`.
- `alembic_version` is **not** in SQLAlchemy metadata. If tests ever hit `nh` and drop tables, Alembic can think migrations are applied while tables are gone — fix with `DROP TABLE alembic_version;` then `alembic upgrade head`.

---

## Demo credentials (dev only)

- Admin UI: `http://localhost:3000/admin/login`
- Seed admin: `admin@nh.example` / `nh-admin` (internal team, not restaurateur).
- Seed restaurant: **Chicken Street Paris**, table label **14** + opaque token.
- JWT secret: see `.env.example` (`JWT_SECRET`). Dev default is fine locally; change before any real deploy.

---

## Public menu (S3)

- Diner URL: `http://localhost:3000/t/<public_token>` — replace `<public_token>` with the real value from DB/admin (e.g. `CUVvNHFlaMkSo8_z9Yy16w`). Opening the literal text `<token>` → « Menu introuvable ».
- API: `GET /t/<token>/menu` — available products only; unknown/inactive token → 404.
- Admin: create tables + download QR PNG (`PUBLIC_WEB_BASE_URL` baked into QR, default `http://localhost:3000`).
- Rebuild api/web images after S3 for Compose to serve new routes.

| Session | Done when |
|---|---|
| S0 | Health + Compose up |
| S1 | Models + migrate + seed |
| S2 | Admin JWT + menu CRUD UI |
| S3 | Tables/QR + public `/t/<token>` menu (read) |
| S4 | Cart → order → confirmation |
| S5–S6 | Cuisine + realtime |
| S10 | Full parcours 13 Sep |

---

## Log

| Date | Note |
|---|---|
| 2026-08-30 | CDC v0.1, technical answers, PDF toolchain. |
| 2026-09-03 | S0 skeleton + Compose; synthèse rule. |
| 2026-09-06 | S1 schema/seed; S2 admin; tests isolated on `nh_test`; 1oo9: useful agent notes → this file. |
| 2026-09-06 | S3: public menu by token + admin tables/QR PNG. |
