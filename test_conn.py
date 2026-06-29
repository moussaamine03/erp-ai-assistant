from backend.db.conn import get_connection, execute_query

# Test 1 : connexion simple
conn = get_connection()
if conn:
    print("✅ Connexion MySQL réussie !")
    conn.close()

# Test 2 : exécuter une requête sur la vue facturation
try:
    results = execute_query("SELECT * FROM vw_facturation LIMIT 5")
    print(f"✅ Vue OK — {len(results)} lignes retournées")
    for row in results[:2]:
        print(row)
except Exception as e:
    print(f"❌ Erreur : {e}")