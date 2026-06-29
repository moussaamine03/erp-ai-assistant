import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import re

load_dotenv()

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Erreur connexion MySQL : {e}")
        return None


def execute_query(sql: str, max_rows: int = 500):
    sql_clean = sql.strip().upper()
    if not sql_clean.startswith("SELECT"):
        raise ValueError("⛔ Seules les requêtes SELECT sont autorisées.")

    conn = get_connection()
    if conn is None:
        raise ConnectionError("❌ Impossible de se connecter à la base de données.")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()        # ← fetchall complet
        return results[:max_rows]          # ← limiter après
    except Error as e:
        raise RuntimeError(f"❌ Erreur SQL : {e}")
    finally:
        cursor.close()
        conn.close()




def len_result(sql: str):
    """
    Exécute une requête SQL en lecture seule
    et retourne le nombre réel de lignes.
    """
    # Sécurité : bloquer toute requête non SELECT
    sql_clean = sql.strip().upper()
    if not sql_clean.startswith("SELECT"):
        raise ValueError("⛔ Seules les requêtes SELECT sont autorisées.")

    # Supprimer la clause LIMIT (LIMIT n ou LIMIT n,m)
    sql = re.sub(
        r"\s+LIMIT\s+\d+(\s*,\s*\d+)?\s*;?\s*$",
        "",
        sql,
        flags=re.IGNORECASE
    )

    conn = get_connection()
    if conn is None:
        raise ConnectionError("❌ Impossible de se connecter à la base de données.")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        if len(results)!=None:
            return len(results)
        else:
            return 0
    except Error as e:
        raise RuntimeError(f"❌ Erreur SQL : {e}")
    finally:
        cursor.close()
        conn.close()