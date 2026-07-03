import json
from backend.llm.llm1 import analyze_intent
from backend.llm.llm2 import generate_sql, generate_sql_multiple
from backend.db.conn import execute_query
from backend.db.conn import len_result
from mistralai import Mistral
from dotenv import load_dotenv
from backend.llm.rate_limiter import mistral_limiter
from backend.llm.llm1 import check_period_availability
import os
from datetime import datetime
import time 

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")

def get_log_file_path():
    """
    Retourne le chemin du fichier de log du jour.
    Ex : logs/ask_history_2026-07-03.json
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"ask_history_{today_str}.json")

def save_to_log(result: dict):
    """
    Sauvegarde chaque interaction dans un fichier JSON distinct par jour.
    """
    log_file = get_log_file_path()

    # Créer le dossier logs si inexistant
    os.makedirs(LOG_DIR, exist_ok=True)

    # Charger l'historique du jour existant
    history = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    # Ajouter la nouvelle entrée
    entry = {
        "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question":      result.get("question"),
        "view":          result.get("view"),
        "sql":           result.get("sql"),
        "success":       result.get("success"),
        "nb_results":    len(result.get("results", []) or []),
        "temps_reponse": result.get("temps_reponse"),
        "response":      result.get("response")
    }
    history.append(entry)

    # Sauvegarder dans le fichier du jour
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2, default=str)
def is_multiple_entities(analysis: dict) -> bool:
    """Détecte si la question concerne plusieurs entités"""
    intent  = analysis.get("intent", "").lower()
    filters = analysis.get("filters", "").lower()
    keywords = [" et ", " and ", " ou ", ",", "plusieurs", "deux", "trois", "multiple"]
    return any(kw in intent or kw in filters for kw in keywords)


def format_response(question: str, sql: str, results: list, real_counts: dict = None) -> str:
    """
    Transforme les résultats SQL bruts en réponse métier.
    Affiche d'abord les résultats réels puis les enrichit.
    """
    if not results:
        return "Aucun résultat trouvé pour votre question."

    total_reel = len(results)
    grouped_str      = ""
    totaux_par_entite = ""
    grouped_data      = {}

    if real_counts:
        remaining = list(results)
        for entite_key, count in real_counts.items():
            chunk = remaining[:count]
            remaining = remaining[count:]

            # ✅ Utiliser DIRECTEMENT entite_key comme titre
            # (déjà extrait depuis le WHERE par le pipeline)
            grouped_data[entite_key] = {"count": count, "rows": chunk}

        totaux_par_entite = "\n⚠️ TOTAUX RÉELS PAR ENTITÉ (NE PAS COMPTER) :\n"
        for nom, data in grouped_data.items():
            totaux_par_entite += f"  - {nom} : {data['count']} lignes\n"
        totaux_par_entite += f"  - TOTAL GLOBAL : {total_reel} lignes\n"

        for nom, data in grouped_data.items():
            grouped_str += f"\n{'='*50}\n"
            grouped_str += f"SECTION_TITRE: {nom}\n"
            grouped_str += f"SECTION_NOMBRE: {data['count']} lignes\n"
            grouped_str += f"SECTION_DONNÉES:\n"
            grouped_str += json.dumps(data["rows"], ensure_ascii=False,
                                    indent=2, default=str)
            grouped_str += f"\n{'='*50}\n"
    else:
        # ── Cas simple ──
        grouped_str = json.dumps(results, ensure_ascii=False,
                                 indent=2, default=str)

    system_prompt = """Tu es un assistant ERP expert en textile.
Tu reçois des résultats RÉELS de base de données.
⚠️ RÈGLES CRITIQUE :
1-jamis changer le resultat obtenu par la requette sql il faut afficher resluts comme il est attention ne supprimer aucuune colonne mentionné dans la requette 
2-toujous afficher les resultat sous forme de tableau attention 
RÈGLES STRICTES :
1. ⚠️ Utiliser UNIQUEMENT les totaux fournis — NE JAMAIS COMPTER
2. Ne jamais inventer ou estimer des chiffres
3. Ne montre jamais le SQL
4. Utilise des emojis pour la lisibilité


RÈGLE DE STRUCTURE — SELON LA DEMANDE UTILISATEUR :
→ Identifier ce que l'utilisateur demande (clients, familles, articles, factures...)
→ Grouper les résultats UNIQUEMENT selon l'entité demandée 


Exemples :
- "factures du client AZUR et A.J" → grouper par CLIENT
- "articles des familles Soutien Gorge et Slip" → grouper par FAMILLE
- "détail des factures F-25/048 et F-25/050" → grouper par FACTURE
- "articles de couleur NOIR et BLANC" → grouper par COULEUR
- "factures impayées" (question simple) → PAS de groupement, liste directe

Structure pour cas MULTIPLES (selon l'entité demandée) :
---
### 🏢 [Entité demandée 1] — Nom
- Nombre : X résultats (chiffre fourni)
- Liste ou tableau des données
- Sous-total si pertinent

---
### 🏢 [Entité demandée 2] — Nom
- Nombre : Y résultats (chiffre fourni)
- Liste ou tableau des données
- Sous-total si pertinent

---
### 📊 Synthèse globale
- Total général : X + Y = Z résultats (chiffres fournis)
- Comparaison ou points clés
---

Structure pour cas SIMPLE :
- Nombre total réel
- Liste ou tableau des résultats
- Synthèse finale
"""

    user_prompt = f"""Question : {question}

{totaux_par_entite}
DONNÉES RÉELLES SÉPARÉES PAR ENTITÉ :
{grouped_str}

INSTRUCTIONS :
- Utiliser UNIQUEMENT les totaux fournis — NE PAS RECALCULER
- Afficher chaque entité séparément avec son titre
- Total global : {total_reel} lignes
"""
    mistral_limiter.wait_if_needed()
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.1
    )

    llm_response = response.choices[0].message.content.strip()

    # ── Header des vrais totaux injecté en tête ──────────────
    totaux_header = f"📊 **Total : {total_reel} résultats**"
    if grouped_data:
        totaux_header += "\n"
        for nom, data in grouped_data.items():
            totaux_header += f"  • **{nom}** : {data['count']} lignes\n"

    return f"{totaux_header}\n\n{llm_response}"

def ask(question: str) -> dict:
    """
    Pipeline complet :
    Question → LLM1 → LLM2 → MySQL → Réponse métier
    """
    sql=None 
    start_time = time.time()  # ← démarrage du chrono
    try:
        # Étape 1 : Analyse de l'intention
        analysis = analyze_intent(question)

        # Cas : question vague → propositions
        if analysis.get("vague") or analysis.get("type") == "vague":
            comprehension = analysis.get("comprehension", "")
            propositions  = analysis.get("propositions", [])
            props_text = "\n".join(
                f"{i+1}. {p}" for i, p in enumerate(propositions)
            )
            duration = round(time.time() - start_time, 2)
            save_to_log({
                 "success": True,
                "question": question,
                "view": None,
                "sql": None,
                "temps_reponse": duration,
                "response": f"🤔 **Votre question manque de détails.**\n\n"
                            f"💡 J'ai compris : *{comprehension}*\n\n"
                            f"Voici des questions plus précises que vous pourriez poser :\n\n"
                            f"{props_text}"
            })
            return {
                "success": True,
                "question": question,
                "view": None,
                "sql": None,
                "response": f"🤔 **Votre question manque de détails.**\n\n"
                            f"💡 J'ai compris : *{comprehension}*\n\n"
                            f"Voici des questions plus précises que vous pourriez poser :\n\n"
                            f"{props_text}"
            }

        # Cas : hors périmètre
        if "error" in analysis:
            duration = round(time.time() - start_time, 2)
            save_to_log({
                "success": False,
                "question": question,
                "view": None,
                "sql": None,
                "temps_reponse": duration,
                "response": "❌ Cette question est hors du périmètre du système.\n\n"
                            "Je peux répondre aux questions sur :\n"
                            "  📄 La facturation (factures, règlements, CA clients)\n"
                            "  🏷️ Les articles (caractéristiques, tailles, familles)\n"
                            "  🔗 Les articles facturés (croisement facturation + articles)"
            })
            return {
                "success": False,
                "question": question,
                "view": None,
                "sql": None,
                "response": "❌ Cette question est hors du périmètre du système.\n\n"
                            "Je peux répondre aux questions sur :\n"
                            "  📄 La facturation (factures, règlements, CA clients)\n"
                            "  🏷️ Les articles (caractéristiques, tailles, familles)\n"
                            "  🔗 Les articles facturés (croisement facturation + articles)"
            }
        
        # Cas : entités inconnues → propositions
        if analysis.get("type") == "unknown_entities":
            unknown  = analysis.get("unknown", {})
            response_text = "⚠️ **Certains termes n'ont pas été trouvés dans la base.**\n\n"

            for valeur, info in unknown.items():
                props = info.get("propositions", [])
                if props:
                    props_text = "\n".join(
                        f"  {i+1}. **{p}**" for i, p in enumerate(props)
                    )
                    response_text += (
                        f"❓ *\"{valeur}\"* non trouvé.\n"
                        f"Voulez-vous dire :\n{props_text}\n\n"
                    )
                else:
                    response_text += (
                        f"❌ *\"{valeur}\"* introuvable dans la base "
                        f"— aucune suggestion disponible.\n\n"
                    )

            response_text += "💡 *Reformulez votre question avec le bon terme.*"
            duration = round(time.time() - start_time, 2)
            save_to_log({
                "success":  True,
                "question": question,
                "view":     None,
                "sql":      None,
                "temps_reponse": duration,
                "response": response_text
            })
            return {
                "success":  True,
                "question": question,
                "view":     None,
                "sql":      None,
                "response": response_text
            }
        
        # ✅ Étape 1.5 : Vérification période — INDÉPENDANTE
        
        period_unknown = check_period_availability(
            analysis.get("view", ""),
            analysis.get("filters", "") or "",
            question  # ← utiliser la question originale, pas l'intent
        )
        if period_unknown:
            response_text = "⚠️ **Aucune donnée trouvée pour la période demandée.**\n\n"
            for periode, info in period_unknown.items():
                props = info.get("propositions", [])
                if props:
                    props_text = "\n".join(f"  {i+1}. **{p}**" for i, p in enumerate(props))
                    response_text += (
                        f"❓ Aucune donnée pour **{periode}**.\n"
                        f"Périodes disponibles :\n{props_text}\n\n"
                    )
            response_text += "💡 *Reformulez votre question avec une période disponible.*"
            duration = round(time.time() - start_time, 2)
            save_to_log({
                "success":  True,
                "question": question,
                "view":     None,
                "sql":      None,
                "temps_reponse": duration,
                "response": response_text
            })
            return {
                "success":  True,
                "question": question,
                "view":     None,
                "sql":      None,
                "response": response_text
            }
                
        nbln =0
        # Étape 2 : Détecter entités multiples ou simple
        if is_multiple_entities(analysis):
            sql_list = generate_sql_multiple(analysis)
            results  = []
            all_sql  = []
            # Stocker les vrais totaux par requête
            real_counts = {}

            for sql_item in sql_list:
                rows = execute_query(sql_item)
                # Extraire l'entité depuis le WHERE
                import re
                match = re.search(r"LIKE\s+'%(.+?)%'|=\s+'(.+?)'", sql_item)
                entite = match.group(1) or match.group(2) if match else f"Entité {len(real_counts)+1}"
                real_counts[entite] = len(rows)
                results.extend(rows)
                all_sql.append(sql_item)

            sql = "\n\n".join(all_sql)

            # Passer les vrais totaux à format_response
            response = format_response(question, sql, results, real_counts)
        else:
            
            sql     = generate_sql(analysis)
            results = execute_query(sql)
            nbln=len_result(sql)
            response = format_response(question, sql, results)

        duration = round(time.time() - start_time, 2)
        save_to_log({
            "success": True,
            "question": question,
            "view": analysis.get("view"),
            "sql": sql,
            "nombre_reele" : nbln,
            "temps_reponse": duration,
            "results": results,
            "response": response
        })
        return {
            "success": True,
            "question": question,
            "view": analysis.get("view"),
            "sql": sql,
            "nombre_reele" : nbln,
            "results": results,
            "response": response
        }

    except Exception as e:
        # Message technique détaillé → uniquement dans le log
        error_detail = f"❌ Erreur : {str(e)}"

        # Message générique → renvoyé à l'utilisateur
        user_message = "⚠️ Un problème est survenu. Veuillez contacter l'administration."
        duration = round(time.time() - start_time, 2)
        save_to_log({
            "success": False,
            "question": question,
            "view": None,
            "sql": sql,
            "temps_reponse": duration,
            "response":error_detail
        })
        return {
            "success": False,
            "question": question,
            "view": None,
            "sql": sql,
            "response": user_message
        }
    

