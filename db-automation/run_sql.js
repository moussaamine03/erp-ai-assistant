/**
 * run_sql.js
 * Script unique, cross-platform (Windows / Linux / Mac).
 * Exécute un fichier .sql donné en argument contre MySQL.
 * Remplace refresh_rh.sh / refresh_rh.ps1 / run_views_startup.sh /
 * run_views_startup.ps1 par un seul mécanisme.
 *
 * Usage :
 *   node run_sql.js sql/rh_tables_refresh.sql
 *   node run_sql.js sql/views_startup.sql
 *
 * Variables d'environnement (.env dans le même dossier) :
 *   DB_HOST (def 127.0.0.1), DB_PORT (def 3306),
 *   DB_USER, DB_PASSWORD, DB_NAME
 */
const fs = require("fs");
const path = require("path");
const mysql = require("mysql2/promise");
require("dotenv").config({ path: path.join(__dirname, ".env") });

const sqlFileArg = process.argv[2];
if (!sqlFileArg) {
  console.error("[FATAL] Usage: node run_sql.js <fichier.sql>");
  process.exit(1);
}

const sqlFilePath = path.isAbsolute(sqlFileArg)
  ? sqlFileArg
  : path.join(__dirname, sqlFileArg);

if (!fs.existsSync(sqlFilePath)) {
  console.error(`[FATAL] Fichier introuvable : ${sqlFilePath}`);
  process.exit(1);
}

const { DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME } = process.env;
// DB_PASSWORD n'est PAS vérifié ici : une chaîne vide est valide
// (ex: root sans mot de passe en local). On vérifie juste qu'il est
// bien défini (même vide) dans le .env, pas qu'il est "truthy".
if (!DB_USER || !DB_NAME || DB_PASSWORD === undefined) {
  console.error("[FATAL] DB_USER, DB_PASSWORD et DB_NAME doivent être définis dans .env");
  process.exit(1);
}

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

async function main() {
  const sql = fs.readFileSync(sqlFilePath, "utf8");
  log(`Exécution de ${path.basename(sqlFilePath)}...`);

  const connection = await mysql.createConnection({
    host: DB_HOST || "127.0.0.1",
    port: DB_PORT ? Number(DB_PORT) : 3306,
    user: DB_USER,
    password: DB_PASSWORD,
    database: DB_NAME,
    multipleStatements: true, // requis pour exécuter tout le fichier en une fois
  });

  try {
    await connection.query(sql);
    log("Terminé avec succès.");
  } finally {
    await connection.end();
  }
}

main().catch((err) => {
  console.error(`[ERREUR] ${err.message}`);
  process.exit(1);
});