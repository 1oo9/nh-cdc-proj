# Proposition technique — MVP commande QR

| | |
|---|---|
| **Projet** | NH — commande restaurant par QR code de table |
| **Document** | Réponses aux questions du cahier des charges |
| **Destinataire** | NH |
| **Auteur** | 1oo9 |
| **Date** | 30 août 2026 |
| **Statut** | Proposition — à valider |
| **Lié à** | `docs/CAHIER_DES_CHARGES.md` v0.1 |

---

## En bref

Nous proposons une **application web** (pas d’app à télécharger) en trois surfaces — **menu client** (téléphone), **cuisine** (tablette), **admin interne** (notre équipe) — branchées sur une API unique et une base **PostgreSQL**.

Le QR code d’une table n’est qu’une URL contenant un **jeton opaque**. Ce jeton identifie à la fois le restaurant et la table. Aucun compte convive. Aucune donnée personnelle de client stockée.

Le **paiement en ligne (Stripe) est hors MVP**. Il pourra être branché plus tard. En v1, la commande arrive en cuisine ; l’encaissement reste celui du restaurant.

**Planning :** objectif **1 à 2 semaines** pour un MVP installable dans **un** restaurant réel, avant le 14 septembre, si le périmètre ci-dessous reste figé.

---

## 1. Architecture

Trois interfaces, une API, une base, isolation par restaurant dès le premier jour.

```
Téléphone (convive)   ── HTTPS ──►  Next.js     menu, panier, confirmation
Tablette (cuisine)    ── HTTPS+WS ► FastAPI     tickets + temps réel
Admin interne         ── HTTPS ──►  Next.js  ──► FastAPI
                                               │
                                          PostgreSQL
                                               │
                                            Redis        pub/sub WebSocket
```

- **Client :** pas d’authentification. La session = le jeton du QR → restaurant + table.
- **Cuisine :** accès simple à la tablette du restaurant (pas de « compte restaurateur » en v1).
- **Admin :** réservé à notre équipe (email + mot de passe).
- **Multi-restaurants :** chaque ligne métier porte un `restaurant_id`. Un seul déploiement pour le MVP ; la montée en charge plus tard est un sujet d’infra, pas de modèle.

Pas de microservices. Un monorepo suffit.

---

## 2. Stack

Piste retenue, proche de celle que tu as proposée :

| Couche | Choix |
|---|---|
| Frontend | Next.js + TypeScript + Tailwind |
| Backend | Python / FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2 (async) + Alembic |
| Base | PostgreSQL |
| Temps réel | WebSocket FastAPI + Redis pub/sub |
| Photos menu | stockage objet (S3-compatible) |
| QR | génération côté serveur (PNG / SVG) |
| Paiement | Stripe — **plus tard**, pas dans le MVP |

FastAPI + Pydantic tiennent largement la charge d’un service restaurant (quelques centaines de commandes à l’heure de pointe, tickets cuisine légers). Le goulot ne sera pas la validation JSON, mais le Wi‑Fi de salle et la base.

---

## 3. Base de données

Argent en **centimes entiers**. Statuts en enum. Le client n’envoie **jamais** le numéro de table : seulement le jeton.

**Entités :**

- `restaurants`
- `admin_users` (notre équipe uniquement)
- `tables` — libellé (« 14 ») + `public_token` unique
- `categories`, `products`
- `option_groups`, `options`
- `orders`, `order_items`, `order_item_options`
- `payments` — table prévue, **inutilisée** en v1

**Règles :**

- toute ligne métier porte `restaurant_id` (sauf les admins internes) ;
- le numéro de commande (`#152`) est **par restaurant**, pas global ;
- les prix sont **figés sur la commande** (le menu peut changer ensuite) ;
- la disponibilité d’un produit est revérifiée à la validation, pas seulement à l’ajout au panier ;
- **aucune donnée personnelle de convive** (nom, e-mail, téléphone, identifiant d’appareil). Le panier reste sur le téléphone jusqu’à la validation. La confirmation s’affiche à l’écran, elle n’est pas envoyée par e-mail.

---

## 4. QR codes

Un QR code n’est qu’une URL. Le secret est le **jeton**, pas le numéro de table.

- URL : `https://<domaine>/t/<public_token>`
- Un jeton → un restaurant + une table
- Le numéro de table **n’apparaît pas** dans l’URL (sinon n’importe qui commande pour la table d’à côté)
- L’admin crée la table, génère le jeton, télécharge le QR, on imprime
- QR perdu ou fuité → on **régénère le jeton**, on réimprime ; l’ancienne URL meurt
- Changer de nom de domaine plus tard = réimprimer toutes les puces. On fige un hostname stable **avant** la première impression.

---

## 5. Commandes en temps réel

La tablette cuisine ouvre un WebSocket **limité à son restaurant**.

1. Le convive valide → la commande est enregistrée en statut `nouvelle`.
2. L’API publie l’événement sur le canal `kitchen:{restaurant_id}`.
3. Chaque tablette abonnée affiche le ticket.
4. Les changements de statut (accepter → en préparation → prête → terminée) empruntent le même chemin.

Si le WebSocket tombe (Wi‑Fi de restaurant) : **reprise automatique + polling toutes les 4–5 s**. La cuisine ne doit pas dépendre d’une socket parfaite.

Une tablette ou trois : même canal.

---

## 6. Délai — MVP

Objectif : **1 à 2 semaines calendaires**, pour un premier restaurant réel, avant la rentrée du **14 septembre 2026**.

| Fenêtre | Contenu |
|---|---|
| Semaine 1 | Socle, schéma, admin interne, menu, tables, génération des QR |
| Semaine 2 | Parcours client (téléphone), cuisine tablette, temps réel, mise en ligne, recette sur place |

C’est tenable **si** :

- le périmètre MVP du cahier des charges **ne bouge pas** ;
- pas de paiement en ligne, pas d’app native, pas de compte restaurateur ;
- un seul restaurant à installer ;
- tes retours sur les choix ci-dessus restent rapides.

La vision SaaS (caisse, stocks, fidélité, centaines de restaurants) n’est **pas** dans ces deux semaines. L’architecture est faite pour pouvoir y aller ensuite.

---

## 7. Points techniques à anticiper

**Produit / flux**

- Sans paiement en ligne : l’encaissement reste au restaurant (comptoir / serveur). À confirmer le libellé cuisine (commande à préparer vs déjà payée).
- Double tap sur « Valider » → une seule commande (clé d’idempotence).
- Produit rendu indisponible alors qu’il est encore dans un panier.
- Deux tablettes qui appuient « Accepter » sur le même ticket.

**QR / sécurité / RGPD**

- URL devinable (`/table/14`) = commandes sur la mauvaise table. Jeton opaque uniquement.
- Pas de compte client, donc peu de données perso — on ne loggue pas d’IP au-delà d’une fenêtre opérationnelle courte, pas d’analytics en v1.
- Les photos du menu sont du contenu restaurant, pas des données de convives.

**Terrain**

- Le vrai risque temps réel est le **Wi‑Fi de salle**, pas le protocole WebSocket.
- Poids des photos : à compresser, sinon le menu rame en 4G.
- Les QR imprimés survivent aux déploiements : on n’encode pas une URL de preview provisoire sur les puces.

**Légal (FR), hors MVP sauf demande**

- L’affichage des **allergènes** est une obligation en restauration. Pas dans le périmètre v1 ; à prévoir dès qu’on sert un vrai service si tu veux l’afficher sur le menu.

---

## Décisions déjà actées

- Application web responsive, pas d’application mobile.
- Admin interne seulement (pas d’espace restaurateur en v1).
- Pas de compte convive.
- Paiement en ligne : **plus tard**.
- Données convives : **restriction PII / RGPD** — on ne stocke pas l’identité du client.
- Premier objectif : un restaurant réel, pas une plateforme complète.

---

## Suite

Si cette proposition te convient, on fige le périmètre et on enchaîne sur le développement du MVP.
