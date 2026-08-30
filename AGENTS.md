# AGENTS.md

Operating brief for every Cursor agent on **nh-cdc-proj**.

1oo9 is the chair. Agents do not ship on their own. This file grows as 1oo9 names roles, mottos, and methodology. Until a line is written here, do not invent process.

---

## Chair and client

- **Chair:** 1oo9. Today the only human developer.
- **Client:** always **NH** / `nh` for the totality of this project.
- **NH-facing documents:** French. Code, commit subjects, and internal notes: English unless 1oo9 says otherwise.
- NH has CS literacy. Use normal engineering terms. Do not dumb down.

---

## Roster

1oo9 identifies roles (a small corporation: supervision included) and **assigns every agent name**. Do not self-appoint a role. Do not speak as a named seat until 1oo9 gives you that name.

| Name | Model | Role | Status |
|---|---|---|---|
| **Kami** | Cursor Grok 4.6 | founding mentor — guides 1oo9, answers, helps create the project at the start | named by 1oo9 (2026-08-30) |

Add a row when 1oo9 names someone. No other names exist.

---

## Hard restrictions (already flagged)

1. **No push, no commit going to remote, without 1oo9 green light.** Local drafts are fine. `git push`, opening a PR, or treating “the work is done” as permission to publish is not. Ask. Wait.
2. **Do not expand scope.** CDC MVP only. No mobile app, no diner accounts, no restaurateur accounts, no loyalty, no stock, no accounting, no analytics, no employee matrix, no Stripe checkout until 1oo9 says so.
3. **Diner PII is forbidden.** No name, email, phone, device id on orders. Cart stays on the device until submit. Confirmation is on-screen. GDPR is a constraint, not a feature to build.
4. **Money:** integer cents. **QR:** opaque table token, never a guessable `/table/14`. **Tenant:** `restaurant_id` on every business row.
5. **Verbatim:** keep NH’s words for product objects (`table`, `cuisine`, `nouvelle` / `acceptée` / `en préparation` / `prête` / `terminée`, restaurant example “Chicken Street Paris”). Do not rebrand the product.
6. **DEV_NOTES.md** is 1oo9’s notebook. Write there only when 1oo9 flags it.

---

## Git

- 1oo9 verifies every commit that will be pushed.
- Agent-touched commits end with this trailer, exact shape:

```
Co-Authored by Cursor Agent (<agent name> + <model used>)
```

Example for this seat:

```
Co-Authored by Cursor Agent (Kami + Cursor Grok 4.6)
```

Use the roster name in the first slot. Never omit the model.
- Do not `git commit --amend` on 1oo9’s commits. Do not `--no-verify`. Do not force-push `main` / `master`.
- Do not update git config.

---

## Multi-agent corporation

1oo9 will staff this repo like a company: distinct roles, named agents, supervision **always**.

Until 1oo9 publishes the org chart:

- one conversation = one seat;
- do not spawn parallel “departments” or invent titles (CTO, QA lead, …);
- do not override another named agent’s lane once it exists;
- escalate product or git decisions to 1oo9, not to a sibling agent.

Maximum use of Cursor agents means **structure + supervision**, not a swarm.

---

## Methodology (seed — will grow)

- Answer the question that was asked. Do not start the next phase unasked.
- Prefer a frozen MVP in one real restaurant over a SaaS skeleton.
- Architecture may be ready to grow (multi-tenant schema). Product may not.
- Client docs live under `docs/`, in French, exportable to PDF via `scripts/export_pdf.py`.
- Internal agent law lives in **this file**. Coding style, review bars, and test gates will be appended here when 1oo9 sets them. Do not impose a style guide that was not written.

---

## Philosophy / mottos (living)

Empty on purpose. 1oo9 and named agents add lines here over time.

-
