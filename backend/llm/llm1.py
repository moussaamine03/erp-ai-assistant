import os
import json
from mistralai import Mistral
from dotenv import load_dotenv
from backend.llm.rate_limiter import mistral_limiter

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "../schemas")


def load_schemas() -> dict:
    schemas = {}
    for filename in os.listdir(SCHEMAS_DIR):
        if filename.endswith(".json"):
            name = filename.replace("schema_", "").replace(".json", "")
            with open(os.path.join(SCHEMAS_DIR, filename), "r", encoding="utf-8") as f:
                schemas[name] = json.load(f)
    return schemas


def build_schemas_summary(schemas: dict) -> str:
    summary = ""
    for domain, schema in schemas.items():
        summary += f"\n=== Domaine: {domain.upper()} ===\n"
        for vue in schema.get("vues_disponibles", []):
            summary += f"\nVue: {vue['nom_vue']}\n"
            summary += f"Description: {vue['description']}\n"
            
            summary += f"Cas d'usage:\n"
            for cas in vue.get("cas_usage", []):
                summary += f"  - {cas}\n"
    return summary

# def build_schemas_summary(schemas: dict) -> str:
#     summary = ""
#     for domain, schema in schemas.items():
#         summary += f"\n=== Domaine: {domain.upper()} ===\n"
#         for vue in schema.get("vues_disponibles", []):
#             summary += f"\nVue: {vue['nom_vue']}\n"
#             summary += f"Description: {vue['description']}\n"
#             summary += f"Cas d'usage:\n"
#             for cas in vue.get("cas_usage", []):
#                 summary += f"  - {cas}\n"

#             # ✅ Ajouter les colonnes exactes
#             if "colonnes" in vue:
#                 summary += f"Colonnes disponibles :\n"
#                 for col in vue["colonnes"].keys():
#                     summary += f"  - {col}\n"
#             elif "colonnes_principales" in vue:
#                 summary += f"Colonnes disponibles :\n"
#                 for col in vue["colonnes_principales"]:
#                     summary += f"  - {col}\n"

#     return summary

def get_vue_schema(schemas: dict, vue_name: str) -> dict:
    for domain, schema in schemas.items():
        for vue in schema.get("vues_disponibles", []):
            if vue["nom_vue"] == vue_name:
                return vue
    return {}


def get_all_exemples(schemas: dict) -> str:
    """Retourne tous les exemples de questions disponibles"""
    exemples = []
    for domain, schema in schemas.items():
        for vue in schema.get("vues_disponibles", []):
            for cas in vue.get("cas_usage", []):
                exemples.append(cas)
    return "\n".join(f"  - {e}" for e in exemples)


def handle_vague_question(user_question: str, schemas: dict) -> dict:
    exemples_str = get_all_exemples(schemas)

    system_prompt = f"""Tu es un assistant ERP expert en textile.
Tu reçois une question vague d'un utilisateur.
Tu dois proposer 4 questions CONCRÈTES d'extraction de données depuis la base ERP.

DÉTECTION DE QUESTION VAGUE :
Une question est VAGUE uniquement si elle est très courte et sans contexte.
⚠️ Une question contenant :
  - un numéro de facture (F-XX/XXX)
  - un numéro de bon d'achat (BA-XX/XXX, FA-XX/XXX ou tout format similaire)
  - un nom de client, fournisseur, article ou famille
  N'EST JAMAIS VAGUE même si le format semble inhabituel.

RÈGLES IMPORTANTES :
- Les propositions doivent être des questions qui extraient des données réelles
- Pas de questions générales ou définitions (ex: "c'est quoi une facture ?")
- Chaque question doit demander des chiffres, listes, statuts ou analyses
- Les questions doivent être directement liées au contexte de la question vague
- Inspire-toi des exemples disponibles dans le système

Exemples de questions disponibles dans le système :
{exemples_str}

Réponds UNIQUEMENT en JSON valide avec cette structure :
{{
    "type": "vague",
    "comprehension": "Ce que j'ai compris de votre question en une phrase courte",
    "propositions": [
        "Question d'extraction précise 1 ?",
        "Question d'extraction précise 2 ?",
        "Question d'extraction précise 3 ?",
        "Question d'extraction précise 4 ?"
    ]
}}

Exemples de BONNES propositions :
- "Quelles sont les factures impayées du mois en cours ?"
- "Quel est le chiffre d'affaires total par client cette année ?"
- "Quelles sont les 5 dernières factures émises ?"
- "Quels articles de la famille Soutien Gorge sont actifs ?"

Exemples de MAUVAISES propositions (à éviter) :
- "Qu'est-ce qu'une facture ?"
- "Quels types de factures existent ?"
- "Comment fonctionne la facturation ?"
"""
    mistral_limiter.wait_if_needed()
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        temperature=0.2
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)


def check_period_availability(view_name: str, filters: str, intent: str) -> dict:
    from backend.db.conn import execute_query
    from datetime import datetime
    import re

    if not view_name:
        return {}

    texte = f"{filters} {intent}".lower()
    now   = datetime.now()

    # ── Détecter période mentionnée ──────────────────────────
    annee = None
    mois  = None
    semaine=None
    dets=None

    annees_trouvees = re.findall(r'\b(20\d{2})\b', texte)
    if annees_trouvees:
        annee = int(annees_trouvees[0])
    if any(kw in texte for kw in ["cette année", "cette annee", "année en cours"]):
        annee = now.year
    if any(kw in texte for kw in ["ce mois", "mois en cours", "mois-ci", "mois courant"]):
        mois  = now.month
        annee = now.year
    if any(kw in texte for kw in ["cette semaine", "la semaine derniere ", "semaine courante"]):
        mois  = now.month
        annee = now.year 
        semaine=now.weekday
        dets=1

    mois_map = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }
    noms_mois = {v: k.capitalize() for k, v in mois_map.items()}
    for nom, num in mois_map.items():
        if nom in texte:
            mois = num
            break

    if not annee and not mois and not semaine:
        return {}

    # ── Mapping exact vue → colonne date complète ─────────────
    # Basé sur les schémas JSON réels
    date_col_map = {
        # Facturation
        "vw_facturation":                "DateFacture",
        "vw_facturation_entetes":        "DateFacture",
        "vw_facturation_detail_article": "DateFacture",
        # Achat
        "vw_achat":                      "DateAchat",
        "vw_achat_entetes":              "DateAchat",
        # RH
        "vw_rh_employe":                 "DateLecture",
        "vw_rh_chaine":                  "DateLecture",
        "vw_rh_production":              "DateLecture",
        "vw_rh_of":                      "PremiereLecture",
    }

    col_date = date_col_map.get(view_name)

    if not col_date:
        return {}

    # ── Construire la condition période ───────────────────────
    if annee and mois and semaine:

        periode_label  = f"{noms_mois.get(mois, str(mois))} {annee} {semaine}"
        condition      = f"YEAR({col_date}) = {annee} AND MONTH({col_date}) = {mois} AND WEEK({col_date})"

    if annee and mois:
        periode_label  = f"{noms_mois.get(mois, str(mois))} {annee}"
        condition      = f"YEAR({col_date}) = {annee} AND MONTH({col_date}) = {mois}"
    elif annee:
        periode_label  = str(annee)
        condition      = f"YEAR({col_date}) = {annee}"
    else:
        return {}

    # ── Vérifier si des données existent ─────────────────────
    try:
        result = execute_query(f"""
            SELECT COUNT(*) AS cnt FROM {view_name}
            WHERE {condition}
            LIMIT 1
        """)
        cnt = result[0]["cnt"] if result else 0
    except Exception:
        return {}

    # ── Si vide → proposer périodes disponibles ───────────────
    if cnt == 0:
        try:
            dispo = execute_query(f"""
                SELECT DISTINCT
                    YEAR({col_date})  AS annee,
                    MONTH({col_date}) AS mois
                FROM {view_name}
                ORDER BY annee DESC, mois DESC
                LIMIT 6
            """)
            if dets == 1:
                propositions = [
                    f"Aucune resultat pour cette semaine "
                    
                ]
            else:
                propositions = [
                    f"{noms_mois.get(int(r['mois']), str(r['mois']))} {r['annee']} "
                    for r in dispo if r["annee"] and r["mois"]
                ]
            return {
                periode_label: {
                    "colonne":      col_date,
                    "vue":          view_name,
                    "propositions": propositions
                }
            }
        except Exception:
            pass

    return {}
def check_unknown_entities(analysis: dict) -> dict:
    """
    Vérifie si les entités extraites des filtres existent dans la base.
    Si un mot est inconnu → cherche des propositions similaires.
    Retourne un dict avec les entités inconnues et leurs propositions.
    """
    from backend.db.conn import execute_query

    view_name = analysis.get("view", "")
    filters   = analysis.get("filters", "")
    intent    = analysis.get("intent", "")

    if not filters and not intent:
        return {}

    # Étape 1 : LLM extrait les valeurs des filtres
    system_prompt = """Tu es un extracteur d'entités pour un ERP textile.
Analyse les filtres SQL et l'intention pour extraire les valeurs recherchées.

Retourne UNIQUEMENT un JSON :
{
    "clients":     [{"valeur": "azuree",       "colonne": "NomClient",          "vue": "vw_facturation_entetes"}],
    "articles":    [{"valeur": "4BF12",         "colonne": "CodeArticle",        "vue": "vw_article"}],
    "familles":    [{"valeur": "soutien gorg",  "colonne": "NomFamille",         "vue": "vw_article"}],
    "factures":    [{"valeur": "F-25/999",      "colonne": "NumeroFacture",      "vue": "vw_facturation_entetes"}],
    "fournisseurs":[{"valeur": "tissage mst",   "colonne": "NomFournisseur",     "vue": "vw_achat_entetes"}],
    "achats":      [{"valeur": "BA-25/001",     "colonne": "NumeroAchat",        "vue": "vw_achat_entetes"}],
    "matieres":    [{"valeur": "tissu noir",    "colonne": "DesignationMP",      "vue": "vw_achat"}],
    "employes":    [{"valeur": "ben aali",      "colonne": "NomCompletEmploye",  "vue": "vw_rh_employe"}],
    "chaines":     [{"valeur": "chaine montaage","colonne": "NomChaine",         "vue": "vw_rh_chaine"}],
    "of":          [{"valeur": "OF-25/999",     "colonne": "NumeroOF",           "vue": "vw_rh_of"}],
    "operations":  [{"valeur": "piquaage col",  "colonne": "NomOperation",       "vue": "vw_rh_of"}]
    "gamme":  [{"valeur": "BM216",  "colonne": "NomGamme",       "vue": "vw_rh_of"}]
}

Règles ABSOLUES :
- Extraire UNIQUEMENT les valeurs littérales recherchées par l'utilisateur
- ⚠️ IGNORER complètement : GROUP BY, ORDER BY, HAVING, LIMIT, COUNT, SUM
- ⚠️ Pour les numéros de factures (format F-XX/XXX ou F-CMP-XX/XXX) :
  → colonne TOUJOURS = "NumeroFacture" (jamais IDFacture)
  → vue TOUJOURS = "vw_facturation_entetes"
- ⚠️ IDFacture est un entier — ne jamais l'utiliser pour chercher "F-18/026"
- ⚠️ IDAchat est un entier — ne jamais l'utiliser pour chercher "BA-25/001"
- ⚠️ Pour les numéros de bons d'achat (tout format : BA-XX/XXX, FA-XX/XXX...) :
  → colonne TOUJOURS = "NumeroAchat"
  → vue TOUJOURS = "vw_achat_entetes"
  Si le numéro fourni ne correspond pas à ce format (ex: '75252kjd')
  → l'extraire quand même avec colonne = "NumeroAchat", vue = "vw_achat_entetes"
  → le système vérifiera son existence dans la base et proposera des corrections
- ⚠️ Pour les numéros d'OF (format OF-XX/XXX) :
  → colonne TOUJOURS = "NumeroOF", vue = "vw_rh_of"  
- Pour les employés → colonne = "NomCompletEmploye", vue = "vw_rh_employe"
- Pour les chaînes de montage → colonne = "NomChaine", vue = "vw_rh_chaine"
- Pour les opérations → colonne = "NomOperation", vue = "vw_rh_of"  
- Pour les achats      → colonne = "NumeroAchat",      vue = "vw_achat_entetes"
- Pour les clients      → colonne = "NomClient",      vue = "vw_facturation_entetes"
- Pour les fournisseurs → colonne = "NomFournisseur",  vue = "vw_achat_entetes"
- Pour les articles     → colonne = "CodeArticle",     vue = "vw_article"
- Pour les familles     → colonne = "NomFamille",      vue = "vw_article"
- Pour les matières premières → colonne = "DesignationMP", vue = "vw_achat"
- Pour les codes MP     → colonne = "CodeMP",          vue = "vw_achat"
- Si les filtres contiennent UNIQUEMENT GROUP BY sans valeur littérale → retourner []
- Listes vides [] si aucune entité du type
"""
    mistral_limiter.wait_if_needed()
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Vue : {view_name}\nFiltres : {filters}\nIntention : {intent}"}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        entities = json.loads(raw)
    except Exception:
        return {}
    
    # ⚠️ Vérifier que c'est bien un dict et pas une liste
    if not isinstance(entities, dict):
        return {}

    # Étape 2 : Vérifier existence dans la base + chercher propositions
    unknown = {}

    all_entities = (
        entities.get("clients",      []) +
        entities.get("articles",     []) +
        entities.get("familles",     []) +
        entities.get("factures",     []) +
        entities.get("fournisseurs", []) +
        entities.get("achats",       []) +
        entities.get("matieres",     []) +
        entities.get("employes",     []) +
        entities.get("chaines",      []) +
        entities.get("of",           []) +
        entities.get("operations",   [])+
        entities.get("gamme",   [])
    )

    for entity in all_entities:
        valeur  = entity.get("valeur", "")
        colonne = entity.get("colonne", "")
        vue     = entity.get("vue", view_name)

        if not valeur or not colonne:
            continue

        # Vérifier existence exacte
        try:
            exact = execute_query(f"""
                SELECT COUNT(*) AS cnt
                FROM {vue}
                WHERE TRIM({colonne}) = '{valeur}'
                LIMIT 1
            """)
            if exact and exact[0]["cnt"] > 0:
                continue  # Existe → pas inconnu
        except Exception:
            continue

        # Chercher propositions similaires
        propositions = []

        # LIKE
        try:
            like_results = execute_query(f"""
                SELECT DISTINCT TRIM({colonne}) AS valeur
                FROM {vue}
                WHERE TRIM({colonne}) LIKE '%{valeur}%'
                LIMIT 5
            """)
            propositions += [r["valeur"] for r in like_results]
        except Exception:
            pass

        # SOUNDEX
        try:
            soundex_results = execute_query(f"""
                SELECT DISTINCT TRIM({colonne}) AS valeur
                FROM {vue}
                WHERE SOUNDEX(TRIM({colonne})) = SOUNDEX('{valeur}')
                LIMIT 5
            """)
            for r in soundex_results:
                if r["valeur"] not in propositions:
                    propositions.append(r["valeur"])
        except Exception:
            pass

        if propositions:
            unknown[valeur] = {
                "colonne":      colonne,
                "vue":          vue,
                "propositions": propositions[:5]
            }
        else:
            unknown[valeur] = {
                "colonne":      colonne,
                "vue":          vue,
                "propositions": []
            }
    
    
    return unknown



def analyze_intent(user_question: str) -> dict:
    """
    LLM 1 : Comprend la question utilisateur et identifie
    le bon schéma métier + la vue SQL à utiliser.
    Retourne un dict structuré pour LLM 2.
    """
    schemas = load_schemas()
    schemas_summary = build_schemas_summary(schemas)

    # Extraire les colonnes disponibles depuis le schéma
    colonnes_disponibles_pourllm1 = ""
    if "colonnes" in schemas:
        for col, info in schemas["colonnes"].items():
            colonnes_disponibles += f"  - {col} ({info['type']}) : {info['description']}\n"
    elif "colonnes_principales" in schemas:
        colonnes_disponibles = "\n".join(
            f"  - {col}" for col in schemas["colonnes_principales"]
        )

    system_prompt = f"""Tu es un assistant expert en ERP textile.
Tu analyses les questions des utilisateurs et tu identifies la vue SQL la plus adaptée.

- ⚠️⚠️ RÈGLE CRITIQUE — GROUP BY OBLIGATOIRE (NE JAMAIS IGNORER) :
  AVANT de générer les filters, TOUJOURS vérifier :
  "Est-ce une vue de détail avec une question sur une entité globale ?"
  Si OUI → GROUP BY OBLIGATOIRE, sans exception.

  Vues de détail concernées :
  vw_facturation, vw_facturation_detail_article, vw_rh_production, vw_achat

  ═══════════════════════════════════════════════════════
  CHECKLIST OBLIGATOIRE AVANT CHAQUE GÉNÉRATION SQL :
  ═══════════════════════════════════════════════════════
  [ ] La vue utilisée est-elle une vue de détail ?
  [ ] La question porte-t-elle sur une entité globale (pas ligne par ligne) ?
  [ ] Si les deux cases sont cochées → GROUP BY AJOUTÉ dans filters

  ═══════════════════════════════════════════════════════
  RÈGLES PAR DOMAINE (OBLIGATOIRES) :
  ═══════════════════════════════════════════════════════

  📄 FACTURATION :
    ✅ DOIT avoir GROUP BY → "liste des factures de famille Slip" → GROUP BY IDFacture
    ✅ DOIT avoir GROUP BY → "factures du client AZUR" → GROUP BY IDFacture
    ❌ PAS de GROUP BY    → "détail des articles de la facture F-25/048"

  🏭 RH/PRODUCTION :
    ✅ DOIT avoir GROUP BY → "production journalière de la chaîne A" → GROUP BY DateLecture, NomChaine
    ✅ DOIT avoir GROUP BY → "production par employé ce mois" → GROUP BY IDEmploye, NomCompletEmploye, Matricule
    ✅ DOIT avoir GROUP BY → "opérations réalisées sur l'OF X" → GROUP BY IDOperation, NomOperation
    ❌ PAS de GROUP BY    → "détail de toutes les lectures de l'employé X"

  🛒 ACHAT :
    ✅ DOIT avoir GROUP BY → "liste des achats du fournisseur X" → GROUP BY IDAchat, NumeroAchat
    ✅ DOIT avoir GROUP BY → "matières achetées ce mois" → GROUP BY CodeMP, DesignationMP
    ❌ PAS de GROUP BY    → "détail des lignes du bon d'achat BA-25/001"

  ═══════════════════════════════════════════════════════
  RAPPEL FINAL — INTERDICTIONS ABSOLUES :
  ═══════════════════════════════════════════════════════
  JAMAIS omettre le GROUP BY sur une vue de détail avec question globale.
  JAMAIS ajouter un GROUP BY sur une question de détail ligne par ligne.
  Les colonnes du GROUP BY DOIVENT exister dans "Colonnes disponibles".
  TOUTE réponse sans GROUP BY sur une vue de détail + question globale = ERREUR CRITIQUE.

⚠️ RÈGLE GÉNÉRALE :
- Si la question utilise "journalière", "par jour", "par semaine", "par mois"
  → toujours ajouter GROUP BY sur la colonne de date correspondante
- Si la question utilise "par employé", "par chaîne", "par client", "par fournisseur"
  → toujours ajouter GROUP BY sur l'entité correspondante
- Si la question est une question de détail (mot "détail", numéro spécifique)
  → PAS de GROUP BY

RÈGLE — COLONNES EXACTES PAR VUE RH :
- vw_rh_employe  → quantité = "TotalPiecesJour"   (jamais QuantiteRealisee)
- vw_rh_chaine   → quantité = "TotalPiecesJour"   (jamais QuantiteRealisee)
- vw_rh_of       → quantité = "TotalPiecesOperation" (jamais QuantiteRealisee)
                 → date = PremiereLecture/DerniereLecture (jamais DateLecture)
                 → filtrer par année → utiliser YEAR(PremiereLecture)
- vw_rh_production → quantité = "QuantiteRealisee" (vue détail uniquement)

⚠️ Ne JAMAIS mettre "QuantiteRealisee" dans columns_needed si la vue 
   est vw_rh_employe, vw_rh_chaine ou vw_rh_of

RÈGLE ABSOLUE — COLONNES EXACTES :
- ⚠️ VALEURS EXACTES : utiliser UNIQUEMENT les valeurs décrites dans le schéma fourni
  Ne jamais inventer des valeurs absentes du schéma
- Le champ "columns_needed" doit contenir UNIQUEMENT les noms de colonnes
  EXACTEMENT tels qu'ils figurent dans la liste "Colonnes disponibles" 
  de la vue choisie ci-dessus
- ⚠️ Avant de mettre une colonne dans "columns_needed" ou dans "filters" :
  → Vérifier qu'elle existe EXACTEMENT dans "Colonnes disponibles"
  → Si elle n'existe pas → chercher le nom correct dans la liste
  → Si aucun nom correspondant → ne pas l'inclure
- Ne JAMAIS inventer, abréger ou renommer une colonne
- Exemples INTERDITS :
  gamme → toujours utiliser "NomGamme" (jamais CodeGamme)
  rendement → toujours utiliser "RendementPct" (jamais Rendement, TauxRendement)
  MatriculeEmploye → utiliser "Matricule"
  of → utiliser "NumeroOF"
  NomArticle       → utiliser "DesignationArticle"
  QuantiteProduite → utiliser "QuantiteRealisee"
  DateAchat        → vérifier le nom exact dans le schéma
- Avant de mettre une colonne dans "columns_needed", vérifier qu'elle
  existe EXACTEMENT dans la liste des colonnes du schéma fourni
- Si tu n'es pas sûr du nom exact → utiliser "*" ou laisser vide

RÈGLE — COMPTAGE EMPLOYÉS :
- Pour TOUTE question demandant un nombre/comptage d'employés
  (combien d'employés, nombre d'employés, liste des employés...)
  → TOUJOURS utiliser la vue vw_rh_employe
  → JAMAIS utiliser vw_rh_chaine même si la question mentionne une chaîne
- Exemples :
  ✅ "Combien d'employés sur la chaîne A ?" → vw_rh_employe (filtrer NomChaine = 'A')
  ✅ "Nombre d'employés actifs" → vw_rh_employe
  ❌ "Combien d'employés sur la chaîne A ?" → vw_rh_chaine (INTERDIT)

RÈGLE DE SÉLECTION DES VUES (très important) :
- utiliser la vue vw_rh_employe pour compter le nombre des employees nest pas vw_rh_chaine
- vw_rh_employe → performance et production par employé               
- vw_rh_chaine → production et charge par chaîne de montage  
- vw_rh_of → avancement et opérations par OF
- vw_rh_production → détail ligne par ligne (cas exceptionnels)
- vw_achat → détail des lignes d'achat (MP achetées, quantités, prix)
- vw_achat_entetes → bons d'achat globaux (statut, montants, liste)
- vw_achat_kpi_fournisseur → analyses par fournisseur (CA, encours, top fournisseurs)
- vw_facturation → uniquement si la question concerne le DÉTAIL des lignes (articles, quantités, prix par ligne)
- vw_facturation_entetes → si la question concerne les factures globalement (statut, montant total, liste, impayés, dates)
- vw_facturation_kpi_client → si la question concerne une ANALYSE ou AGRÉGATION par client (CA total, encours, top clients)
- vw_article → si la question concerne les caractéristiques d'un article spécifique
- vw_article_tailles → si la question concerne les tailles disponibles d'un article
- vw_article_kpi_famille → si la question concerne des statistiques par famille d'articles mais sil y a des information lié aux commande utilise la vue vw_facturation_detail_article 
- vw_facturation_detail_article → quand la question croise facturation ET articles :
  ✅ "factures de la famille X"
  ✅ "factures des articles X"
  ✅ "articles facturés de la famille X"
  ✅ "factures contenant des articles de couleur X"
  ✅ Toute question combinant famille/couleur/article AVEC factures
  

RÈGLE ABSOLUE — AUCUNE CONDITION SUPPLÉMENTAIRE :
- "filters" doit contenir UNIQUEMENT les conditions EXPLICITEMENT mentionnées
- Ne JAMAIS ajouter statut, date, état non demandés par l'utilisateur

DÉTECTION DE QUESTION VAGUE :
Une question est VAGUE uniquement si elle est très courte et sans contexte
(ex: "les factures", "les articles", "montre moi quelque chose").

⚠️ Une question N'EST JAMAIS VAGUE si elle contient :
- Un numéro de facture (F-XX/XXX, F-CMP-XX/XXX)
- Un numéro de bon d'achat (BA-XX/XXX, FA-XX/XXX ou tout format alphanumérique)
- Un nom de client, fournisseur, article ou famille
- Une condition temporelle (ce mois, cette année, 2025...)
- Un statut (impayé, réglé, actif...)
- Toute valeur spécifique même si le format est inhabituel

Si vague → retourner {{"vague": true}}
Si hors périmètre → retourner {{"error": "hors périmètre"}}

Vues disponibles :
{schemas_summary}
Colonnes disponibles :
{colonnes_disponibles_pourllm1}


Tu dois répondre UNIQUEMENT en JSON valide avec cette structure :
{{
    "domain": "nom du domaine",
    "view": "nom exact de la vue SQL",
    "intent": "description courte de l'intention",
    "filters": "conditions SQL + GROUP BY si nécessaire",
    "columns_needed": ["colonne1", "colonne2"],
    "schema": {{}}
}}

Règles importantes :
- Utilise UNIQUEMENT les vues listées ci-dessus
- Ne génère PAS de SQL ici, juste l'analyse
"""
    mistral_limiter.wait_if_needed()
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    # Cas vague → générer des propositions
    if result.get("vague"):
        return handle_vague_question(user_question, schemas)

    # Enrichir avec le schéma complet de la vue choisie
    if "view" in result and "error" not in result:
        result["schema"] = get_vue_schema(schemas, result["view"])
        unknown = check_unknown_entities(result)
        if unknown:
            return {
                "type":    "unknown_entities",
                "unknown": unknown,
                "analysis": result  # Garder l'analyse pour après validation
            }        

    return result