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
| mistralai | 2.4.9+ | Client API Mistral |

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
├── sql/
│   ├── vw_facturation.sql
│   ├── vw_article.sql
│   ├── vw_facturation_detail_article.sql
│   ├── vw_achat.sql
│   └── vw_rh_v2.sql
├── logs/
│   └── ask_history.json         # Historique des interactions
├── .env                         # Variables d'environnement
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
git clone <repo>
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

Créer le fichier `.env` :

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

### 4. Créer les vues SQL

Exécuter dans DBeaver dans l'ordre :

```bash
sql/vw_facturation.sql
sql/vw_article.sql
sql/vw_facturation_detail_article.sql
sql/vw_achat.sql
sql/vw_rh.sql
```

### 5. Installer et configurer n8n

```bash
npm install -g n8n
n8n start
```

Importer le workflow n8n :
- Ouvrir `http://localhost:5678`
- Créer un workflow avec 3 nodes :
  - **Webhook** : POST `/erp-assistant`
  - **HTTP Request** : POST `http://127.0.0.1:8000/ask`
  - **Respond to Webhook** : First Incoming Item
- Publier le workflow

---

## ▶️ Lancement

Démarrer les 3 services dans des terminaux séparés :

```bash
# Terminal 1 — n8n
n8n start

# Terminal 2 — FastAPI
cd erp-ai-assistant
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000

# Terminal 3 — Streamlit
streamlit run frontend/app.py
```

Ouvrir : **http://localhost:8501**

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
