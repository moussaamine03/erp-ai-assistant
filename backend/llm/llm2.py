import json
import os
from mistralai import Mistral
from dotenv import load_dotenv
from backend.llm.rate_limiter import mistral_limiter

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def generate_sql_multiple(analysis: dict) -> list:
    """
    Génère une requête SQL séparée pour chaque entité.
    Retourne une liste de strings SQL (même format que generate_sql).
    Ex: ["SELECT ... WHERE NomClient LIKE '%AZUR%'",
         "SELECT ... WHERE NomClient LIKE '%A.J%'"]
    """
    view_name      = analysis.get("view", "")
    intent         = analysis.get("intent", "")
    filters        = analysis.get("filters", "")
    columns_needed = analysis.get("columns_needed", [])
    schema         = analysis.get("schema", {})

    colonnes_disponibles = ""
    if "colonnes" in schema:
        for col, info in schema["colonnes"].items():
            colonnes_disponibles += f"  - {col} ({info['type']}) : {info['description']}\n"
    elif "colonnes_principales" in schema:
        colonnes_disponibles = "\n".join(
            f"  - {col}" for col in schema["colonnes_principales"]
        )

    system_prompt = f"""Tu es un expert SQL pour base de données MySQL.
Tu génères UNE requête SQL séparée pour CHAQUE entité mentionnée.

RÈGLE — COUNT AVEC DISTINCT :
- Pour compter des entités uniques, toujours utiliser COUNT(DISTINCT colonne)
- Exemples :
  ✅ Nombre d'employés     → COUNT(DISTINCT IDEmploye) ou COUNT(DISTINCT Matricule)
  ✅ Nombre de factures    → COUNT(DISTINCT IDFacture) ou COUNT(DISTINCT NumeroFacture)
  ✅ Nombre de clients     → COUNT(DISTINCT IDClient) ou COUNT(DISTINCT NomClient)
  ✅ Nombre d'OF           → COUNT(DISTINCT IDOFabrication) ou COUNT(DISTINCT NumeroOF)
  ✅ Nombre de fournisseurs → COUNT(DISTINCT IDFournisseur) ou COUNT(DISTINCT NomFournisseur)
  ❌ COUNT(Matricule)      → peut compter des doublons si vue agrégée
  ❌ COUNT(*)              → compte toutes les lignes pas les entités uniques
- Pour les vues agrégées (vw_rh_employe, vw_rh_chaine, vw_rh_of) :
  utiliser TOUJOURS COUNT(DISTINCT IDEmploye) pour compter les employés

RÈGLE — GROUP BY :
- Si les "Filtres suggérés" mentionnent un GROUP BY → l'ajouter OBLIGATOIREMENT
  dans la requête SQL générée
- Le GROUP BY doit contenir toutes les colonnes SELECT non agrégées
- Les colonnes numériques mentionnées avec SUM/COUNT → utiliser ces fonctions
- Exemple si filters contient "GROUP BY IDFacture (SUM Quantite)" :
  SELECT IDFacture, NumeroFacture, DateFacture, NomClient, 
         SUM(Quantite) AS QuantiteTotale
  FROM vue
  WHERE ...
  GROUP BY IDFacture, NumeroFacture, DateFacture, NomClient

- Si GROUP BY présent → ne pas ajouter DISTINCT (redondant)


RÈGLE — LIMIT AUTOMATIQUE :
- Questions globales sans filtre spécifique (pas de client/fournisseur/numéro précis)
  → Ajouter LIMIT 100 automatiquement
- Questions avec filtre spécifique (un client, un numéro, une famille précise)
  → Pas de LIMIT 
- Questions d'agrégation (SUM, COUNT, AVG)
  → Pas de LIMIT
- Questions de type TOP/classement
  → Respecter le nombre demandé (ex: TOP 5 → LIMIT 5)

Exemples :

✅ "factures du client AZUR" → filtre client précis → pas de LIMIT 
✅ "CA total par fournisseur" → agrégation → pas de LIMIT
✅ "top 5 fournisseurs" → LIMIT 5

RÈGLE ABSOLUE :

- Ne jamais utiliser des colonnes qui ne sont pas dans la liste des colonnes disponibles
- ⚠️ COLONNES INTERDITES RH  :
  MatriculeEmploye  → utiliser Matricule
  NomArticle        → utiliser NomGamme ou NomOperation
  QuantiteProduite  → utiliser QuantiteRealisee
  IDEmployeNum      → utiliser IDEmploye
  DateProduction    → utiliser DateLecture
- ⚠️ COLONNES INTERDITES ACHAT :
  IDBonAchat       → NumeroAchat
  NomMatierePremiere → DesignationMP
  IDMatierePremiere  → IDMP
  QuantiteAchetee    → Quantite
  StatutPaiement     → StatutReglement
- Une entité = une requête SQL indépendante
- Retourner UNIQUEMENT un JSON — liste de strings SQL
- Chaque string SQL doit être complète et indépendante
- JAMAIS utiliser IN, OR, UNION pour regrouper plusieurs entités
- ⚠️ VALEURS EXACTES : utiliser UNIQUEMENT les valeurs décrites dans le schéma fourni
  Ne jamais inventer des valeurs absentes du schéma
  Exemples corrects :
    EtatArticle     → 'Actif' ou 'Inactif'  (jamais 'Disponible', 'Active', 'En stock')
    StatutReglement → 'Totalement réglé', 'Non réglé', 'Partiellement réglé'
    TypeProduit     → 'Semi-fini' ou 'Produit fini'
    NatureArticle   → 'Matière première' ou 'Article'


Exemple pour 2 factures F-18/018 et F-19/025 :
[
  "SELECT col1, col2 FROM {view_name} WHERE TRIM(NumeroFacture) = 'F-18/018'",
  "SELECT col1, col2 FROM {view_name} WHERE TRIM(NumeroFacture) = 'F-19/025'"
]

Exemple pour 2 clients AZUR et A.J :
[
  "SELECT col1, col2 FROM {view_name} WHERE TRIM(NomClient) LIKE '%AZUR%' ORDER BY DateFacture DESC",
  "SELECT col1, col2 FROM {view_name} WHERE TRIM(NomClient) LIKE '%A.J%' ORDER BY DateFacture DESC"
]

INTERDIT :
❌ WHERE NumeroFacture IN ('F-18/018', 'F-19/025')
❌ WHERE NomClient LIKE '%X%' OR NomClient LIKE '%Y%'
❌ UNION ALL entre les entités

RÈGLES SQL :
- Utiliser UNIQUEMENT la vue : {view_name}
- SELECT uniquement
- TRIM() sur les colonnes varchar
- LIKE '%valeur%' pour les noms
- = pour les codes et numéros exacts
- Valeurs exactes du schéma uniquement

Vue : {view_name}
Colonnes disponibles :
{colonnes_disponibles}

Répondre UNIQUEMENT avec le JSON — liste de strings SQL, sans markdown.
"""

    user_prompt = f"""Intention : {intent}
Filtres : {filters}
Colonnes souhaitées : {', '.join(columns_needed) if columns_needed else 'toutes les colonnes pertinentes'}

Génère UNE requête SQL par entité mentionnée.
Chaque requête doit être indépendante et complète.
Retourne uniquement la liste JSON de strings SQL."""
    
    mistral_limiter.wait_if_needed()
    response = client.chat.complete(
        model="codestral-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    sql_list = json.loads(raw)

    # Validation sécurité
    for sql in sql_list:
        if not sql.upper().strip().startswith("SELECT"):
            raise ValueError(f"⛔ Requête non autorisée : {sql[:50]}")

    return sql_list

def generate_sql(analysis: dict) -> str:
    """
    LLM 2 : Reçoit l'analyse de LLM 1 et génère
    la requête SQL précise à exécuter.
    Utilise Codestral (optimisé pour la génération de code/SQL).
    """
    view_name = analysis.get("view", "")
    intent = analysis.get("intent", "")
    filters = analysis.get("filters", "")
    columns_needed = analysis.get("columns_needed", [])
    schema = analysis.get("schema", {})

    # Extraire les colonnes disponibles depuis le schéma
    colonnes_disponibles = ""
    if "colonnes" in schema:
        for col, info in schema["colonnes"].items():
            colonnes_disponibles += f"  - {col} ({info['type']}) : {info['description']}\n"
    elif "colonnes_principales" in schema:
        colonnes_disponibles = "\n".join(
            f"  - {col}" for col in schema["colonnes_principales"]
        )

    system_prompt = f"""Tu es un expert SQL pour base de données MySQL.
Tu génères des requêtes SQL précises et optimisées.

RÈGLE — COUNT AVEC DISTINCT :
- Pour compter des entités uniques, toujours utiliser COUNT(DISTINCT colonne)
- Exemples :
  ✅ Nombre d'employés     → COUNT(DISTINCT IDEmploye) ou COUNT(DISTINCT Matricule)
  ✅ Nombre de factures    → COUNT(DISTINCT IDFacture) ou COUNT(DISTINCT NumeroFacture)
  ✅ Nombre de clients     → COUNT(DISTINCT IDClient) ou COUNT(DISTINCT NomClient)
  ✅ Nombre d'OF           → COUNT(DISTINCT IDOFabrication) ou COUNT(DISTINCT NumeroOF)
  ✅ Nombre de fournisseurs → COUNT(DISTINCT IDFournisseur) ou COUNT(DISTINCT NomFournisseur)
  ❌ COUNT(Matricule)      → peut compter des doublons si vue agrégée
  ❌ COUNT(*)              → compte toutes les lignes pas les entités uniques
- Pour les vues agrégées (vw_rh_employe, vw_rh_chaine, vw_rh_of) :
  utiliser TOUJOURS COUNT(DISTINCT IDEmploye) pour compter les employés
  
RÈGLE — GROUP BY :
- Si les "Filtres suggérés" mentionnent un GROUP BY → l'ajouter OBLIGATOIREMENT
  dans la requête SQL générée
- Le GROUP BY doit contenir toutes les colonnes SELECT non agrégées
- Les colonnes numériques mentionnées avec SUM/COUNT → utiliser ces fonctions
- Exemple si filters contient "GROUP BY IDFacture (SUM Quantite)" :
  SELECT IDFacture, NumeroFacture, DateFacture, NomClient, 
         SUM(Quantite) AS QuantiteTotale
  FROM vue
  WHERE ...
  GROUP BY IDFacture, NumeroFacture, DateFacture, NomClient

- Si GROUP BY présent → ne pas ajouter DISTINCT (redondant)

RÈGLES ABSOLUES :
- Utiliser UNIQUEMENT la vue : {view_name}
- Requêtes SELECT uniquement (jamais INSERT, UPDATE, DELETE)

- Utiliser TRIM() pour les champs varchar lors des comparaisons
- Utiliser LIKE '%valeur%' pour les recherches par nom client
- Les colonnes doivent exister dans la vue
- ⚠️ VALEURS EXACTES : utiliser UNIQUEMENT les valeurs décrites dans le schéma fourni
  Ne jamais inventer des valeurs absentes du schéma
  Exemples corrects :
    EtatArticle     → 'Actif' ou 'Inactif'  (jamais 'Disponible', 'Active', 'En stock')
    StatutReglement → 'Totalement réglé', 'Non réglé', 'Partiellement réglé'
    TypeProduit     → 'Semi-fini' ou 'Produit fini'
    NatureArticle   → 'Matière première' ou 'Article'
- Si une valeur de filtre n'est pas dans le schéma, utiliser LIKE à la place

RÈGLE — LIMIT AUTOMATIQUE :
- Questions globales sans filtre spécifique (pas de client/fournisseur/numéro précis)
  → Ajouter LIMIT 100 automatiquement
- Questions avec filtre spécifique (un client, un numéro, une famille précise)
  → Pas de LIMIT 
- Questions d'agrégation (SUM, COUNT, AVG)
  → Pas de LIMIT
- Questions de type TOP/classement
  → Respecter le nombre demandé (ex: TOP 5 → LIMIT 5)

Exemples :

✅ "factures du client AZUR" → filtre client précis → pas de LIMIT
✅ "CA total par fournisseur" → agrégation → pas de LIMIT
✅ "top 5 fournisseurs" → LIMIT 5

Vue à utiliser : {view_name}
Colonnes disponibles :
{colonnes_disponibles}

Tu dois répondre UNIQUEMENT avec la requête SQL pure.
Sans explication, sans markdown, sans backticks.
La réponse doit commencer directement par SELECT.
"""

    user_prompt =f"""Intention : {intent}
Filtres suggérés : {filters}
Colonnes souhaitées : {', '.join(columns_needed) if columns_needed else 'toutes les colonnes pertinentes'}

RÈGLES POUR LES CAS MULTIPLES :
- Si la question concerne PLUSIEURS clients → utiliser UNION ALL pour garantir
  les résultats de chaque client séparément :

  (SELECT colonnes FROM vue WHERE TRIM(NomClient) LIKE '%Client1%' ORDER BY DateFacture DESC )
  UNION ALL
  (SELECT colonnes FROM vue WHERE TRIM(NomClient) LIKE '%Client2%' ORDER BY DateFacture DESC )

- Ne jamais utiliser un seul WHERE avec OR pour plusieurs clients
- Pour les codes articles → utiliser IN avec TRIM
- Pour les numéros factures → utiliser IN avec TRIM
- Toujours utiliser TRIM() sur les colonnes varchar

Génère la requête SQL optimisée."""
    
    mistral_limiter.wait_if_needed()
    response = client.chat.complete(
        model="codestral-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )

    sql = response.choices[0].message.content.strip()

    # Nettoyage si markdown
    if "```" in sql:
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    sql = sql.strip()

    # Sécurité : vérifier que c'est bien un SELECT
    if not sql.upper().startswith("SELECT"):
        raise ValueError(f"⛔ Requête non autorisée générée : {sql[:50]}")

    return sql