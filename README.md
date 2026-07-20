# 🧵 ERP AI Copilot — Textile

> Assistant intelligent en langage naturel pour ERP textile, basé sur une architecture multi-LLM, n8n et Streamlit.

---

## 📋 Table des matières

- [Présentation](#présentation)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Besoins métier couverts](#besoins-métier-couverts)
- [Pipeline de traitement](#pipeline-de-traitement)
- [Installation](#installation)
- [Lancement](#lancement)
- [Configuration](#configuration)
- [Fonctionnalités MVP](#fonctionnalités-mvp)

---

## 🎯 Présentation

L'ERP AI Copilot est un assistant conversationnel qui permet aux utilisateurs d'interroger leur **ERP textile** en langage naturel. Il traduit automatiquement les questions en requêtes SQL, les exécute sur la base de données, et retourne une réponse métier compréhensible.

### Exemples de questions supportées

```
"Quelles sont les factures impayées ?"
"Top 5 employés par rendement ce mois ?"
"Quels articles de la famille Soutien Gorge ont été facturés à AZUR ?"
"Quels achats ne sont pas encore réglés ?"
"Quel est le rendement de la chaîne Houda Hajji ?"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                              │
│              (Interface Streamlit)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   n8n (Orchestrateur)                       │
│         Webhook → HTTP Request → Respond                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /ask
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI (Backend)                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   LLM 1      │    │   LLM 2      │    │   Pipeline   │  │
│  │ Mistral Small│───▶│  Codestral   │───▶│  MySQL       │  │
│  │ Analyse      │    │  Génération  │    │  Exécution   │  │
│  │ Intention    │    │  SQL         │    │  SQL         │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Business Layer (Vues SQL)                      │
│  vw_facturation · vw_article · vw_achat · vw_rh_*          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Base de données MySQL (ERP Textile)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack technique

### Backend

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.9+ | Langage principal |
| FastAPI | latest | API REST backend |
| Uvicorn | latest | Serveur ASGI |
| mysql-connector-python | latest | Connexion MySQL |
| python-dotenv | latest | Variables d'environnement |
| mistralai | 1.5.0 | Client API Mistral |

### LLM

| Modèle | Rôle | Provider |
|--------|------|----------|
| `mistral-small-latest` | LLM 1 — Analyse intention, détection entités, formatage réponse | Mistral API |
| `codestral-latest` | LLM 2 — Génération SQL optimisée | Mistral API |

### Orchestration & Frontend

| Outil | Version | Rôle |
|-------|---------|------|
| n8n | 2.8.4+ | Orchestrateur workflow (Webhook → FastAPI) |
| Streamlit | latest | Interface chat utilisateur |
| requests | latest | Appels HTTP depuis Streamlit |

### Base de données

| Outil | Rôle |
|-------|------|
| MySQL | Base de données ERP textile |
| DBeaver | Administration et gestion des vues SQL |

---
## 📁 Structure du projet

```
erp-ai-assistant/
├── backend/
│   ├── db/
│   │   ├── __init__.py
│   │   └── conn.py              # Connexion MySQL + execute_query
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm1.py              # LLM 1 : analyse intention + détection entités
│   │   ├── llm2.py              # LLM 2 : génération SQL
│   │   └── rate_limiter.py      # Rate limiter Mistral API
│   ├── schemas/
│   │   ├── schema_facturation.json
│   │   ├── schema_article.json
│   │   ├── schema_facturation_article.json
│   │   ├── schema_achat.json
│   │   └── schema_rh.json
│   ├── pipeline.py              # Pipeline complet Ask()
│   └── main.py                  # FastAPI endpoints
├── frontend/
│   └── app.py                   # Interface Streamlit
├── db-automation/               # Orchestration SQL (vues + tables RH)
│   ├── run_sql.js               # Exécuteur SQL cross-platform (remplace .sh/.ps1)
│   ├── package.json
│   ├── .env                     # Identifiants MySQL (propre à db-automation)
│   └── sql/
│       ├── views_startup.sql        # Vues Facturation, Article, Achat
│       └── rh_tables_refresh.sql    # Tables RH_Production (refresh quotidien)
├── logs/
│   └── ask_history.json         # Historique des interactions
├── my_workflow.json             # Workflow n8n à importer
├── ecosystem.config.js          # Configuration PM2 (backend, frontend, n8n, vues, RH)
├── .env                         # Variables d'environnement (backend)
├── requirements.txt
└── README.md
```

---

## 📊 Besoins métier couverts

### ✅ Facturation
| Vue | Description |
|-----|-------------|
| `vw_facturation` | Détail lignes factures + articles |
| `vw_facturation_entetes` | Entêtes factures (statut, montants, clients) |
| `vw_facturation_kpi_client` | KPI agrégés par client |
| `vw_facturation_detail_article` | Croisement factures × articles |

### ✅ Articles
| Vue | Description |
|-----|-------------|
| `vw_article` | Caractéristiques complètes articles |
| `vw_article_tailles` | Articles × tailles disponibles |
| `vw_article_kpi_famille` | KPI agrégés par famille |

### ✅ Achats
| Vue | Description |
|-----|-------------|
| `vw_achat` | Détail lignes achats + matières premières |
| `vw_achat_entetes` | Entêtes bons d'achat |
| `vw_achat_kpi_fournisseur` | KPI agrégés par fournisseur |

### ✅ RH / Production
| Vue | Description |
|-----|-------------|
| `vw_rh_employe` | Production et rendement par employé/jour |
| `vw_rh_chaine` | Production et charge par chaîne/jour |
| `vw_rh_of` | Avancement et opérations par OF |
| `vw_rh_production` | Détail ligne par ligne (lectures) |

---

## 🔄 Pipeline de traitement

```
Question utilisateur
        │
        ▼
┌───────────────────┐
│  LLM 1 (Mistral)  │  → Analyse intention
│  analyze_intent   │  → Identifie vue SQL
│                   │  → Extrait filtres
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ check_unknown     │  → Vérifie entités (clients, fournisseurs...)
│ check_period      │  → Vérifie disponibilité des périodes
└─────────┬─────────┘
          │
          ├── Question vague → Propositions
          ├── Entité inconnue → Suggestions
          ├── Période absente → Périodes disponibles
          │
          ▼
┌───────────────────┐
│  LLM 2 (Codestral)│  → Génère requête SQL précise
│  generate_sql     │  → Simple ou multiple (UNION)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  MySQL            │  → Exécution SQL sécurisée
│  execute_query    │  → SELECT uniquement
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  pipeline(Mistral)│  → Formate réponse métier
│  format_response  │  → Structurée par entité
└─────────┬─────────┘
          │
          ▼
     Réponse finale
```

---
## 🚀 Installation

### 1. Cloner et créer l'environnement

```bash
git clone https://github.com/moussaamine03/erp-ai-assistant.git
cd erp-ai-assistant
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

Créer le fichier `.env` à la racine :

```env
# Mistral API
MISTRAL_API_KEY=votre_clé_api_mistral

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=nom_de_votre_base
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
```

### 4. Créer les vues et tables SQL (via db-automation)

Les vues et tables ne sont plus créées manuellement dans DBeaver — `db-automation` s'en charge de façon reproductible sur Windows comme sur Linux.

```bash
cd db-automation
npm install
cp .env.example .env      # remplir avec les identifiants MySQL (peuvent être identiques au .env racine)
```

Puis exécuter :

```bash
# Vues métier : Facturation, Article, Achat
node run_sql.js sql/views_startup.sql

# Tables RH_Production (matérialisées, pas des vues)
node run_sql.js sql/rh_tables_refresh.sql
```

> Ces deux commandes sont idempotentes : elles peuvent être rejouées sans risque. `views_startup.sql` recrée les vues à chaque lancement du projet ; `rh_tables_refresh.sql` reconstruit les tables RH et sera rafraîchi automatiquement chaque jour via PM2 (voir section Lancement).

### 5. Installer et configurer n8n

```bash
npm install -g n8n
```

#### Lancer n8n

```bash
# Windows / Mac
n8n start

# Linux (désactiver le cookie sécurisé si accès via HTTP)
N8N_SECURE_COOKIE=false n8n start
```

#### Importer le workflow

Le fichier `my_workflow.json` à la racine du projet contient le workflow n8n préconfiguré.

1. Ouvrir n8n dans le navigateur :
   - En local : `http://localhost:5678`
   - Sur serveur : `http://IP_DU_SERVEUR:5678`
2. Aller dans **Workflows** → **Import from file**
3. Sélectionner `my_workflow.json`
4. Vérifier les ports dans le workflow :
   - Le node **HTTP Request** doit pointer vers `http://127.0.0.1:8000/ask`
   - Si le port FastAPI a été changé, mettre à jour cette URL dans le node HTTP Request
5. **Activer le workflow** (toggle en haut à droite)

> ⚠️ Le webhook n8n sera disponible sur le port **5678** par défaut. Si ce port est occupé, n8n en choisira un autre — vérifier le terminal au démarrage.

---
## ▶️ Lancement

### Option 1 — Manuel (test / développement)

Démarrer les services dans des terminaux séparés :

```bash
# Terminal 1 — n8n
N8N_SECURE_COOKIE=false n8n start   # Linux
n8n start                            # Windows

# Terminal 2 — FastAPI
cd erp-ai-assistant
source venv/bin/activate             # Linux
venv\Scripts\activate                # Windows
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 3 — Streamlit
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

> Les vues et tables SQL (`db-automation`) doivent avoir été exécutées au moins une fois avant de démarrer le backend (voir Installation étape 4). En mode manuel, il n'y a pas de rafraîchissement automatique quotidien des tables RH — relancer `node run_sql.js sql/rh_tables_refresh.sql` manuellement si besoin, ou utiliser l'Option 2 (PM2) pour l'automatiser.

Ouvrir : **http://localhost:8501** (local) ou **http://IP_DU_SERVEUR:8501** (serveur)

### Option 2 — PM2 (production / serveur)

Le fichier `ecosystem.config.js` à la racine du projet configure **5 process** PM2 :

| Process | Rôle | Déclenchement |
|---|---|---|
| `views-startup` | Recrée les vues Facturation/Article/Achat | Une fois, au lancement |
| `rh-refresh` | Reconstruit les tables RH_Production | Tous les jours à 02:00 |
| `erp-backend` | API FastAPI | Continu (autorestart) |
| `erp-frontend` | Interface Streamlit | Continu (autorestart) |
| `erp-n8n` | Serveur n8n | Continu (autorestart) |

```bash
# Lancer tous les services (ordre respecté : vues/tables SQL avant backend/frontend)
cd erp-ai-assistant
pm2 start ecosystem.config.js

# Vérifier le statut
pm2 status

# Voir les logs
pm2 logs
pm2 logs views-startup
pm2 logs rh-refresh

# Redémarrer un service
pm2 restart erp-backend
pm2 restart erp-frontend
pm2 restart erp-n8n
pm2 restart rh-refresh      # forcer un refresh RH immédiat, hors planning 02:00

# Arrêter tous les services
pm2 stop all

# Sauvegarder la config pour redémarrage automatique au boot
pm2 save
pm2 startup
```

> ⚠️ Les ports par défaut dans `ecosystem.config.js` sont **8000** (FastAPI), **8501** (Streamlit) et **5678** (n8n). Si tu changes un port, pense à mettre à jour le node HTTP Request dans le workflow n8n.
> 
> ⚠️ `views-startup` et `rh-refresh` s'exécutent puis se terminent (`autorestart: false`) — les voir en statut `stopped` dans `pm2 status` est normal, ce n'est pas une erreur.

---

## ⚙️ Configuration avancée

### Rate Limiter Mistral

Dans `backend/llm/rate_limiter.py` :

```python
# Ajuster selon votre plan Mistral
mistral_limiter = RateLimiter(max_calls=1, period=3.0)
```

### Sécurité SQL

- Seules les requêtes `SELECT` sont autorisées
- Aucun accès direct aux tables — uniquement via les vues métier
- Pas de `DELETE`, `UPDATE`, `INSERT`

### Logs

Les interactions sont sauvegardées dans `logs/ask_history.json` :

```json
{
  "timestamp": "2025-06-01 10:30:00",
  "question": "Quelles sont les factures impayées ?",
  "view": "vw_facturation_entetes",
  "sql": "SELECT ...",
  "success": true,
  "nb_results": 46,
  "response": "📊 46 factures impayées..."
}
```

---

## ✅ Fonctionnalités MVP

| Fonctionnalité | Status |
|----------------|--------|
| Chat en langage naturel | ✅ |
| Identification automatique de la vue SQL | ✅ |
| Génération SQL sécurisée | ✅ |
| Réponse métier formatée | ✅ |
| Détection questions vagues | ✅ |
| Correction orthographique (fuzzy matching) | ✅ |
| Vérification disponibilité périodes | ✅ |
| Questions composées (multi-entités) | ✅ |
| Interface Streamlit mode clair/sombre | ✅ |
| Historique des conversations | ✅ |
| Rate limiting API Mistral | ✅ |
| 4 domaines métier | ✅ |
| n8n comme orchestrateur | ✅ |
| Logs JSON des interactions | ✅ |

---

## 👨‍💻 Développé avec

- **Mistral AI** — LLM pour la compréhension et génération
- **n8n** — Orchestration workflow
- **FastAPI** — Backend Python
- **Streamlit** — Interface utilisateur
- **MySQL** — Base de données ERP textile

---

*ERP AI Copilot — Stage été 2025 · Industrie Textile*
