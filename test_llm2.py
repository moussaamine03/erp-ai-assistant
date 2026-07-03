from backend.llm.llm1 import analyze_intent
from backend.llm.llm2 import generate_sql

questions = [
    # "Quel est le chiffre d'affaires total du client Dupont ?",
    # "Montre-moi les détails des articles de la facture F-25/048",
    # "Quelles sont les factures impayées ?",
    #  "Nombre d'employés de la chaîne Houda Hajji",
    "Quel est le chiffre d'affaires total facturé à AZUR en 2025",

]

for q in questions:
    print(f"\n❓ Question : {q}")
    analysis = analyze_intent(q)
    print(f"🔍 Vue : {analysis.get('view')}")
    sql = generate_sql(analysis)
    print(f"✅ SQL généré :\n{sql}")
    print("-" * 50)