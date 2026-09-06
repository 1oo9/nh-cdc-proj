# Commande restaurant par QR de table

Dépôt du projet **NH** : une plateforme de commande pour restaurants, basée sur un **QR code unique par table**. Le convive scanne, commande depuis son téléphone, **sans compte** et **sans application à installer**. La cuisine reçoit le ticket en direct.

**Décisions techniques validées le 3 septembre 2026.**  
**Objectif :** un MVP **testable** (parcours complet) d’ici le **13 septembre 2026**, pour un **premier restaurant réel**. La rentrée du 14 septembre n’est pas une journée de développement.

Documents destinés à NH : **français**.

---

## Ce que le produit fait

Chaque table a un QR. Le scan ouvre le menu **déjà rattaché à cette table et à ce restaurant**.

Exemple : restaurant *Chicken Street Paris*, table 14 → toute commande issue de ce QR arrive en cuisine comme **table 14**.

```
QR → Menu → Catégorie → Produit → Options → Panier → Validation → Confirmation
                                                                      ↓
                                                              Cuisine (tablette)
                                                    nouvelle → acceptée → en préparation
                                                              → prête → terminée
```

Trois surfaces, une seule application web :

| Surface | Qui | Support | Rôle |
|---|---|---|---|
| **Client** | le convive | téléphone | consulter, personnaliser, commander, voir la confirmation |
| **Cuisine** | le personnel | tablette | voir les tickets, changer le statut, sans F5 si le Wi‑Fi tient |
| **Admin** | notre équipe (pas le restaurateur en v1) | ordinateur | restaurants, menu, prix, photos, options, tables, QR |

Le restaurateur nous contacte pour une modification de menu ; on la fait dans l’admin.

---

## Choix figés (v1)

| Sujet | Décision |
|---|---|
| Forme | Application **web** responsive — pas d’app native |
| Frontend | Next.js + TypeScript + Tailwind |
| Backend | Python / FastAPI + Pydantic v2 |
| Base | PostgreSQL — un `restaurant_id` sur chaque ligne métier |
| Temps réel | WebSocket + Redis ; si la socket tombe, **polling 4–5 s** |
| QR | URL `https://<domaine>/t/<jeton>` — le jeton est opaque, **pas** le numéro de table |
| Argent | Prix en **centimes entiers** ; le prix est **figé sur la commande** |
| Compte convive | aucun |
| Compte restaurateur | aucun en v1 |
| Paiement en ligne (Stripe) | **plus tard** — l’encaissement reste celui du restaurant |
| Données convives | **aucune** (pas de nom, e-mail, téléphone). RGPD : le panier reste sur le téléphone jusqu’à validation ; la confirmation s’affiche à l’écran |
| Premier déploiement | **un** restaurant — le modèle est déjà multi-restaurants |

Pas de microservices. Un monorepo : API + web + Postgres + Redis.

```
Téléphone     ── HTTPS ──►  Next.js      menu, panier, confirmation
Tablette      ── HTTPS+WS ► FastAPI      tickets + live
Admin interne ── HTTPS ──►  Next.js  ──► FastAPI
                                        │
                                   PostgreSQL
                                        │
                                     Redis
```

---

## Données

Entités prévues : restaurants, admins internes, tables, catégories, produits, options / suppléments, commandes, lignes de commande, paiements (table **vide** en v1), statuts.

Règles importantes :

- le client n’envoie **jamais** le numéro de table, seulement le jeton du QR ;
- le `#` de commande est **par restaurant** (`#152` chez A n’est pas `#152` chez B) ;
- un produit retiré du menu après ajout au panier est **refusé à la validation** ;
- QR perdu → on régénère le jeton, l’ancienne URL meurt, on réimprime.

---

## Périmètre MVP

**Inclus**

- Client : QR, menu, catégories, produits, photos, options, panier, commande, confirmation
- Cuisine : réception, table, détail, statuts, temps réel (avec filet de polling)
- Admin interne : restaurants, menu, produits, options, tables, génération des QR

**Hors v1** (vision SaaS, plus tard)

- application mobile, compte client, espace restaurateur
- Stripe / paiement en ligne
- fidélité, stocks, caisse, comptabilité, analytics, gestion d’employés
- allergènes à l’affichage (obligation FR — à prévoir avant un vrai service si tu le demandes)

---

## Calendrier (à partir du 3 septembre)

| Quand | Ce que tu pourras vérifier |
|---|---|
| 3–4 sept. | Socle qui démarre (API + site + base) |
| 5–6 sept. | Admin : on crée un menu et des tables ; le téléphone **lit** le menu via le jeton |
| 7–9 sept. | Commande réelle en base + écran cuisine + apparition live |
| 10–12 sept. | Cas limites (double validation, mauvais jeton, produit indisponible) + démo sur deux appareils |
| **13 sept.** | **Recette** : parcours complet QR → cuisine `terminée` |
| 14 sept. | Rentrée — pas de nouvelle fonctionnalité |

Si le calendrier glisse, on coupe le polish et un éventuel hébergement cloud. On **ne coupe pas** la commande ni le live cuisine.

---

## Documents

| Fichier | Contenu |
|---|---|
| [docs/CAHIER_DES_CHARGES.md](docs/CAHIER_DES_CHARGES.md) | Besoin tel que formulé (v0.1) |
| [docs/PROPOSITION_TECHNIQUE.md](docs/PROPOSITION_TECHNIQUE.md) | Réponses aux 7 questions (architecture, stack, BDD, QR, live, délai, risques) |
| [docs/syntheses/](docs/syntheses/) | Comptes rendus de session (un PDF à envoyer à NH à chaque fin de session) |

Export PDF (mise en page conservée) :

```bash
.venv/bin/python scripts/export_pdf.py
```

Les PDF sortent dans `docs/pdf/` (non versionnés).

---

## Lancer le socle

Branche de travail : **`tableos`**. TDD : `pytest` (API) et `vitest` (web) avant toute fonctionnalité.

**Compose** (Postgres + Redis + api + web) :

```bash
docker compose up --build -d
```

**API (hôte, contre la Postgres Compose)**

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

`GET http://localhost:8000/health` → `{"status":"ok"}`  
Seed démo : restaurant **Chicken Street Paris**, table **14** (jeton opaque), burgers / accompagnements / boissons.  
Admin interne : [http://localhost:3000/admin/login](http://localhost:3000/admin/login) — `admin@nh.example` / `nh-admin`  
Menu client (lecture) : `http://localhost:3000/t/<jeton>` — jeton opaque de la table (admin → Tables & QR).

**Web**

```bash
cd apps/web
npm install
npm test
npm run dev
```

`http://localhost:3000` affiche `API ok` si l’API tourne.

Variables : copier `.env.example`. Redis est allumé ; le code applicatif ne l’utilise qu’à partir de S6.

**Dev en chaise :** 1oo9.
