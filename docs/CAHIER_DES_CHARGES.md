# Cahier des charges — Plateforme de commande QR (tables)

| | |
|---|---|
| **Projet** | NH — commande restaurant par QR code de table |
| **Document** | Cahier des charges (CDC) |
| **Version** | 0.1 — structuration du brief initial |
| **Statut** | Analyse / discussion — pas encore figé |
| **Source** | Brief original de NH (non modifié sur le fond) |
| **Langue** | Français (documents destinés à NH) |
| **Dev en chaise** | 1oo9 |
| **Branche** | `tableos` |

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Concept](#2-concept)
3. [Interface client](#3-interface-client)
4. [Interface cuisine](#4-interface-cuisine)
5. [Interface administration](#5-interface-administration)
6. [Données](#6-données)
7. [Fonctionnement d’une commande](#7-fonctionnement-dune-commande)
8. [Technologie (piste NH)](#8-technologie-piste-nh)
9. [Périmètre MVP](#9-périmètre-mvp)
10. [Hors périmètre (v1)](#10-hors-périmètre-v1)
11. [Objectif final (vision)](#11-objectif-final-vision)
12. [Questions de NH — à trancher avant le dev](#12-questions-de-nh--à-trancher-avant-le-dev)

---

## 1. Présentation

NH souhaite développer une **plateforme de commande pour restaurants**, basée sur des **QR codes placés directement sur les tables**.

Le client ( convive ) scanne le QR, consulte le menu, commande depuis son téléphone — **sans compte** et **sans application à télécharger**.

La première version est un **MVP**, destiné à être installé dans **un restaurant réel** pour valider l’usage (clients + personnel). La vision long terme est une **plateforme SaaS** multi-restaurants.

---

## 2. Concept

Chaque table du restaurant possède un **QR code unique**.

Le client scanne le QR avec son téléphone et arrive directement sur le menu du restaurant, **déjà rattaché à sa table**.

Il peut ensuite :

1. Consulter le menu
2. Voir les catégories et les produits
3. Consulter les photos, descriptions et prix
4. Choisir des options / suppléments
5. Ajouter les produits à son panier
6. Valider sa commande
7. Éventuellement payer directement en ligne
8. Recevoir une confirmation de commande

**Contraintes produit (explicites) :**

- aucun compte client ;
- aucune application native à installer ;
- le QR identifie **à la fois le restaurant et la table**.

**Exemple :**

| | |
|---|---|
| Restaurant | Chicken Street Paris |
| Table | 14 |

Lorsqu’une commande est passée, le système sait automatiquement qu’elle vient de la **table 14**.

---

## 3. Interface client

Interface **principalement pensée pour téléphone**.

**Parcours cible :**

```
QR code → Menu → Catégorie → Produit → Personnalisation → Panier → Validation → Confirmation
```

Application **web responsive** (pas d’app mobile native en v1).

---

## 4. Interface cuisine

Deuxième interface, destinée à la **cuisine**, utilisée sur **tablette**.

Lorsqu’une nouvelle commande est passée, elle **apparaît automatiquement** à l’écran.

**Exemple d’affichage :**

```
COMMANDE #152
TABLE 14

2 × Chicken Burger
    * fromage

1 × Frites
2 × Coca-Cola

TOTAL : 24,50 €

[ACCEPTER]
```

**Statuts de commande (après acceptation / tout au long du cycle) :**

| Statut | |
|---|---|
| Nouvelle | commande reçue, pas encore prise en charge |
| Acceptée | cuisine a accepté |
| En préparation | en cours |
| Prête | prête à être servie / récupérée |
| Terminée | cycle clos |

La mise à jour doit **idéalement être en temps réel**, sans rafraîchir la page.

---

## 5. Interface administration

Le restaurant **ne dispose pas** d’un espace administrateur dans la première version.

C’est **l’équipe projet** qui gère les menus pour les restaurants. Le restaurateur contacte l’équipe lorsqu’il veut modifier son menu ; la modification se fait depuis cette interface.

Interface d’administration **privée**, permettant de :

- créer un restaurant ;
- modifier les informations du restaurant ;
- créer / modifier / supprimer des catégories ;
- créer / modifier / supprimer des produits ;
- modifier les prix ;
- modifier les descriptions ;
- ajouter / modifier les photos ;
- créer des options et suppléments ;
- rendre un produit disponible ou indisponible ;
- modifier l’ordre des produits ;
- créer les différentes tables ;
- générer les QR codes correspondants.

**Arborescence cible :**

```
Restaurant
  → Catégories
  → Produits
  → Options
  → Tables
  → QR codes
```

---

## 6. Données

Structure prévue pour **plusieurs restaurants**. Chaque restaurant doit être **complètement séparé** des autres.

Entités nécessaires :

- restaurants
- utilisateurs / admins
- tables
- catégories
- produits
- options / suppléments
- commandes
- produits des commandes
- paiements
- statuts des commandes

---

## 7. Fonctionnement d’une commande

```
Client scanne le QR
        ↓
Le serveur identifie restaurant + table
        ↓
Le client consulte le menu
        ↓
Il crée son panier
        ↓
Il valide
        ↓
La commande est enregistrée
        ↓
La cuisine reçoit instantanément la commande
        ↓
La cuisine accepte
        ↓
La commande passe en préparation
        ↓
La commande est prête
        ↓
La commande est terminée
```

---

## 8. Technologie (piste NH)

NH part sur une **application web responsive** plutôt qu’une application mobile.

Il laisse proposer l’architecture la plus adaptée, avec une exigence : assez propre pour **évoluer ensuite vers plusieurs centaines / milliers de restaurants**.

**Stack envisagée par NH (ouverte aux contre-propositions) :**

| Couche | Piste |
|---|---|
| Frontend | React / Next.js |
| Backend | Python / FastAPI |
| BDD | PostgreSQL |
| Temps réel | WebSocket |
| Paiement | Stripe |

---

## 9. Périmètre MVP

**Règle :** ne pas développer une énorme plateforme d’emblée. La v1 contient **uniquement** le nécessaire pour tester le concept avec un vrai restaurant.

### Client

- QR code
- Menu
- Catégories
- Produits
- Photos
- Options / suppléments
- Panier
- Passage de commande
- Confirmation

### Cuisine

- Réception des commandes
- Affichage de la table
- Détail de la commande
- Changement de statut
- Actualisation en temps réel

### Admin (interne)

- Gestion des restaurants
- Gestion du menu
- Gestion des produits
- Gestion des options
- Gestion des tables
- Génération des QR codes

---

## 10. Hors périmètre (v1)

À ne **pas** développer pour l’instant :

- application mobile
- compte client
- compte restaurateur
- système de fidélité
- gestion avancée des stocks
- comptabilité
- analytics avancés
- gestion complexe des employés

Ces fonctionnalités pourront venir plus tard si le concept fonctionne.

---

## 11. Objectif final (vision)

Le but n’est pas seulement un menu QR.

À terme : une **plateforme SaaS** pour restaurants :

```
QR code
  → commande
  → paiement
  → cuisine
  → caisse
  → stocks
  → statistiques
  → fidélité
```

**Objectif immédiat :** un MVP suffisamment propre pour l’installer dans un **premier restaurant réel**, et voir si les clients et le personnel l’utilisent facilement.

---

## 12. Questions de NH — à trancher avant le dev

Avant tout développement, NH demande :

1. Quelle architecture proposer ?
2. Quelle stack utiliser ?
3. Comment organiser la BDD ?
4. Comment gérer les QR codes ?
5. Comment gérer les commandes en temps réel ?
6. Combien de temps estimer pour le MVP ?
7. Quels points techniques problématiques anticiper ?

Réponses rédigées pour NH : [`docs/PROPOSITION_TECHNIQUE.md`](./PROPOSITION_TECHNIQUE.md).
