from backend.pipeline import ask
from backend.llm.llm1 import analyze_intent
# result = analyze_intent("liste des factures du client forum group et Aj")
# print(result)

# questions = [

#     "donner les detailles d'achat FA-23/0002 et FA-23/0003",
#     "Top 5 fournisseurs par volume d'achat",
#     "donner les achats ne sont pas réglés ?",
#     "quelle est la famille darticle la plus demander"
#     " liste des factures de famille slip et bavette ",
#     "liste des factures des client a.j et azur",
#     "donner les articles des factures F-18/018 et F-17/014"
#     "donner les detailles de facture F-19/010 "
#     "Liste des achats du fournisseur Sasi Bousif et Borhene Kouki",
#     "Détail des achats de la matière CDI0018 et CSA0011",
#     " Liste des fournisseurs dont le pays d'origine est la Tunisie"
#     "Quel est le rendement moyen par chaîne de montage ?",
#     "tpo 5 employe par rendement en 2025"
#     "Quelles opérations ont été réalisées sur l'OF 1026907p ?",
#     "Production journalière de l'employé matricule 568",
#     "quel est la famille darticle qui a la plus grande quantite commandé"
#     "Top 5 employés par rendement en 2025",
#     "Quel est le rendement moyen par chaîne de montage ?",
#     "nombre des employe de la chaine Houda Hajji"
#     "Quel employé a produit le plus de pièces en 2025",
#      'Quelle est la production journalière de la chaîne Houda Hajji ?',
#     "Production par semaine de l'employé BEN SGHAIER Sourour"
#     "Quelle est la quantité totale produite de l'opération Prep bret et Emballage",
#     "Quelle gamme est la plus produite ce mois ?",
#     "Combien de pièces ont été produites sur la gamme BM216 par of ?",
    

    
# ]
questions = [

    # Achats & Fournisseurs
    # "Donner les détails d'achat FA-23/0002 et FA-23/0003",
    # "Top 5 fournisseurs par volume d'achat",
    # "liste des achats qui ne sont pas réglés",
    # "Liste des achats du fournisseur Sasi Bousif et Borhene Kouki",
    # "Détail des achats de la matière CDI0018 et CSA0011",
    # "Liste des fournisseurs dont le pays d'origine est la Tunisie",

    # # Ventes & Facturation
    # "Quelle est la famille d'article la plus commandé ?",
    # "Liste des factures de la famille Slip et Bavette",
    # "Liste des factures des clients A.J et Azur",
    # "Donner les articles des factures F-18/018 et F-17/014",
    # "Donner les détails de la facture F-19/010",
    # "Quelle est la famille d'article ayant la plus grande quantité commandée ?",

    # # Production
    # "Quel est le rendement moyen par chaîne de montage ?",
    # "Quelles opérations ont été réalisées sur l'OF 1026907P ?",
    # "Quelle est la quantité totale produite pour les opérations Prep Bret et Emballage ?",
    # "Quelle gamme est la plus produite ce mois ?",
    # "Combien de pièces ont été produites sur la gamme BM216 par OF ?",
    # "production journalière de la chaîne Houda Hajji ?",

    # # RH & Performance
    # "Top 5 employés par rendement cette semaine",
    # "Production journalière de l'employé matricule 568",
    # "Nombre d'employés de la chaîne Houda Hajji",
    # "Quel employé a produit le plus de pièces en 2025 ?",
    # "Production hebdomadaire de l'employé BEN SGHAIER Sourour"
    "Top 5 employés par rendement en 2025"

]

for q in questions:
    print(f"\n{'='*60}")
    print(f"❓ {q}")
    print('='*60)
    result = ask(q)
    
    print(f"🔍 Vue utilisée : {result.get('view')}")
    print(f"📝 SQL :\n{result.get('sql')}")
    print(f"📝 nombre reele :\n{result.get('nombre_reele')}")
    print(f"\n💬 Réponse :\n{result.get('response')}")
   
    


# from backend.llm.llm1 import analyze_intent

# questions = [
#     "liste des factures de famille bavette et slip",
# ]

# for q in questions:
#     print(f"\n❓ {q}")
#     result = analyze_intent(q)
#     print(f"🔍 Type    : {result.get('type')}")
#     print(f"🔍 View    : {result.get('view')}")
#     print(f"🔍 Intent  : {result.get('intent')}")
#     print(f"🔍 Filters : {result.get('filters')}")
#     print(f"🔍 Columns : {result.get('columns_needed')}")    
