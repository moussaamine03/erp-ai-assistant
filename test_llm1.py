from backend.llm.llm1 import analyze_intent

questions = [
    # "Quel est le chiffre d'affaires total du client a.j ?",  # → vw_facturation_kpi_client
    # "Montre-moi les détails des articles de la facture ihf745kk ",   # → vw_facturation
    # "Quels achats ne sont pas réglés ?",
    # "Top 5 fournisseurs par volume d'achat",
    # "donner les detailles d'achat 75252kjd",
    #  "Production journalière de l'employé matricule 568",
    # "Quel est le rendement moyen par chaîne de montage ?",
    # 'Quelle est la production journalière de la chaîne Houda Hajji ?',
# "Quelle gamme est la plus produite cette année ?",
#  "Nombre d'employés de la chaîne Houda Hajji",
# "donne moi la liste des top 10 article en CA",
"Quel est le chiffre d'affaires total facturé à AZUR en 2025",
]


for q in questions:
    print(f"\n❓ Question : {q}")
    result = analyze_intent(q)
    print(f"✅ Analyse : {result}")
    print(f"✅ Vue choisie : {result.get('view')}")
    print(f"✅ Intent : {result.get('intent')}")
    print(f"🔍 Filters : {result.get('filters')}")
    print(f"🔍 Filters : {result.get('schema')}")
from backend.llm.llm1 import analyze_intent

# result = analyze_intent("Quelle est la quantité produite par opération en 2025?")
# print(f"🔍 Vue     : {result.get('view')}")
# print(f"🔍 Filters : {result.get('filters')}")
# print(f"🔍 Columns : {result.get('columns_needed')}")


