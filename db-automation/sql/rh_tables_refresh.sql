-- ============================================================
-- rh_tables_refresh.sql
-- Rafraîchit les 4 tables RH/Production en les recréant.
-- Simple, direct, exécuté 1x/jour par PM2 (cron_restart).
-- ============================================================
SET NAMES utf8mb4;

-- ---------- rh_employe_tbl ----------
DROP TABLE IF EXISTS vw_rh_employe;
CREATE TABLE vw_rh_employe AS
WITH of_par_jour AS (
    SELECT l.IDEmploye, l.Date, SUM(of2.Quantite) AS TotalQuantiteOF
    FROM (
        SELECT DISTINCT IDEmploye, Date, IDOFabrication
        FROM lectures WHERE Date > '2025-01-01' AND IDOFabrication > 0
    ) l
    INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication
    GROUP BY l.IDEmploye, l.Date
)
SELECT
    l.IDEmploye,
    CONCAT(TRIM(e.Nom), ' ', TRIM(e.Prenom)) AS NomCompletEmploye,
    TRIM(e.Nom) AS NomEmploye, TRIM(e.Prenom) AS PrenomEmploye,
    e.Matricule, e.Specialite,
    CASE e.Sexe WHEN 1 THEN 'Homme' WHEN 2 THEN 'Femme' ELSE 'Non défini' END AS Sexe,
    CASE e.Etat WHEN 1 THEN 'Actif' ELSE 'Inactif' END AS EtatEmploye,
    e.TauxHoraire, e.DateEmbauche,
    l.IDChaineMontage,
    TRIM(cm.ChaineMontage) AS NomChaine, cm.Code AS CodeChaine,
    l.Date AS DateLecture, YEAR(l.Date) AS Annee, MONTH(l.Date) AS Mois, WEEK(l.Date) AS Semaine,
    SUM(l.Quantite) AS TotalPiecesJour,
    COUNT(l.IDLectures) AS NbrLectures,
    ROUND(SUM(l.Temps), 2) AS TempsTotal,
    oj.TotalQuantiteOF,
    CASE WHEN oj.TotalQuantiteOF > 0
         THEN ROUND(SUM(l.Quantite) / NULLIF(oj.TotalQuantiteOF, 0) * 100, 2)
         ELSE NULL END AS RendementPct
FROM lectures l
INNER JOIN employe e ON l.IDEmploye = e.IDEmploye AND l.IDEmploye > 0
INNER JOIN chainemontage cm ON l.IDChaineMontage = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN operation op ON l.IDOperation = op.IDOperation AND l.IDOperation > 0
INNER JOIN of_par_jour oj ON l.IDEmploye = oj.IDEmploye AND l.Date = oj.Date
WHERE l.Date > '2025-01-01'
GROUP BY l.IDEmploye, e.Nom, e.Prenom, e.Matricule, e.Specialite,
         e.Sexe, e.Etat, e.TauxHoraire, e.DateEmbauche,
         l.IDChaineMontage, cm.ChaineMontage, cm.Code, l.Date, oj.TotalQuantiteOF;

ALTER TABLE vw_rh_employe
    ADD PRIMARY KEY (IDEmploye, DateLecture, IDChaineMontage),
    ADD INDEX idx_date (DateLecture);

-- ---------- rh_chaine_tbl ----------
DROP TABLE IF EXISTS vw_rh_chaine;
CREATE TABLE vw_rh_chaine AS
WITH of_par_jour_chaine AS (
    SELECT l.IDChaineMontage, l.Date, SUM(of2.Quantite) AS TotalQuantiteOF
    FROM (
        SELECT DISTINCT IDChaineMontage, Date, IDOFabrication
        FROM lectures WHERE Date > '2025-01-01' AND IDOFabrication > 0
    ) l
    INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication
    GROUP BY l.IDChaineMontage, l.Date
)
SELECT
    l.IDChaineMontage,
    TRIM(cm.ChaineMontage) AS NomChaine, cm.Code AS CodeChaine,
    l.Date AS DateLecture, YEAR(l.Date) AS Annee, MONTH(l.Date) AS Mois, WEEK(l.Date) AS Semaine,
    TRIM(of2.OFAbrication) AS NumeroOF,
    CASE of2.Etat WHEN 0 THEN 'En cours' WHEN 1 THEN 'Terminé' WHEN 2 THEN 'Annulé' ELSE 'Inconnu' END AS EtatOF,
    COUNT(DISTINCT l.IDEmploye) AS NbrEmployes,
    SUM(l.Quantite) AS TotalPiecesJour,
    COUNT(l.IDLectures) AS NbrLectures,
    ROUND(SUM(l.Temps), 2) AS TempsTotal,
    oj.TotalQuantiteOF,
    CASE WHEN oj.TotalQuantiteOF > 0
         THEN ROUND(SUM(l.Quantite) / NULLIF(oj.TotalQuantiteOF, 0) * 100, 2)
         ELSE NULL END AS RendementPct
FROM lectures l
INNER JOIN chainemontage cm ON l.IDChaineMontage = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication AND l.IDOFabrication > 0
INNER JOIN operation op ON l.IDOperation = op.IDOperation AND l.IDOperation > 0
INNER JOIN of_par_jour_chaine oj ON l.IDChaineMontage = oj.IDChaineMontage AND l.Date = oj.Date
WHERE l.Date > '2025-01-01'
GROUP BY l.IDChaineMontage, cm.ChaineMontage, cm.Code,
         l.Date, of2.OFAbrication, of2.Etat, oj.TotalQuantiteOF;

ALTER TABLE vw_rh_chaine ADD INDEX idx_chaine_date (IDChaineMontage, DateLecture);

-- ---------- rh_of_tbl ----------
DROP TABLE IF EXISTS vw_rh_of;
CREATE TABLE vw_rh_of AS
SELECT
    l.IDOFabrication,
    TRIM(of2.OFAbrication) AS NumeroOF,
    of2.DtDebut AS DateDebutOF, of2.DtFin AS DateFinOF,
    of2.Quantite AS QuantitePrevueOF, of2.QtteLct AS QuantiteLanceeOF,
    CASE of2.Etat WHEN 0 THEN 'En cours' WHEN 1 THEN 'Terminé' WHEN 2 THEN 'Annulé' ELSE 'Inconnu' END AS EtatOF,
    l.IDChaineMontage,
    TRIM(cm.ChaineMontage) AS NomChaine,
    l.IDOperation,
    TRIM(op.Operation) AS NomOperation, op.Code AS CodeOperation, op.Temps AS TempsPrevuOperation,
    l.IDGamme,
    TRIM(g.Gamme) AS NomGamme, g.TpsGamme AS TempsTotalGamme,
    COUNT(DISTINCT l.IDEmploye) AS NbrEmployes,
    SUM(l.Quantite) AS TotalPiecesOperation,
    ROUND(SUM(l.Temps), 2) AS TempsTotalRealise,
    MIN(l.Date) AS PremiereLecture, MAX(l.Date) AS DerniereLecture
FROM lectures l
INNER JOIN chainemontage cm ON l.IDChaineMontage = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication AND l.IDOFabrication > 0
INNER JOIN operation op ON l.IDOperation = op.IDOperation AND l.IDOperation > 0
INNER JOIN gamme g ON l.IDGamme = g.IDGamme AND l.IDGamme > 0
WHERE l.Date > '2025-01-01' AND l.IDOFabrication > 0
GROUP BY l.IDOFabrication, of2.OFAbrication, of2.DtDebut, of2.DtFin,
         of2.Quantite, of2.QtteLct, of2.Etat, l.IDChaineMontage, cm.ChaineMontage,
         l.IDOperation, op.Operation, op.Code, op.Temps, l.IDGamme, g.Gamme, g.TpsGamme;

ALTER TABLE vw_rh_of ADD PRIMARY KEY (IDOFabrication, IDOperation, IDChaineMontage, IDGamme);

-- ---------- rh_production_tbl ----------
DROP TABLE IF EXISTS vw_rh_production;
CREATE TABLE vw_rh_production AS
SELECT
    l.IDLectures,
    l.Date AS DateLecture, YEAR(l.Date) AS Annee, MONTH(l.Date) AS Mois, WEEK(l.Date) AS Semaine,
    l.IDEmploye,
    CONCAT(TRIM(e.Nom), ' ', TRIM(e.Prenom)) AS NomCompletEmploye,
    TRIM(e.Nom) AS NomEmploye, TRIM(e.Prenom) AS PrenomEmploye,
    e.Matricule, e.Specialite,
    CASE e.Sexe WHEN 1 THEN 'Homme' WHEN 2 THEN 'Femme' ELSE 'Non défini' END AS Sexe,
    CASE e.Etat WHEN 1 THEN 'Actif' ELSE 'Inactif' END AS EtatEmploye,
    e.TauxHoraire, e.DateEmbauche,
    l.IDChaineMontage, TRIM(cm.ChaineMontage) AS NomChaine, cm.Code AS CodeChaine,
    l.IDOFabrication, TRIM(of2.OFAbrication) AS NumeroOF,
    of2.DtDebut AS DateDebutOF, of2.DtFin AS DateFinOF, of2.Quantite AS QuantiteOF,
    CASE of2.Etat WHEN 0 THEN 'En cours' WHEN 1 THEN 'Terminé' WHEN 2 THEN 'Annulé' ELSE 'Inconnu' END AS EtatOF,
    l.IDOperation, TRIM(op.Operation) AS NomOperation, op.Code AS CodeOperation, op.Temps AS TempsPrevuOperation,
    l.IDGamme, TRIM(g.Gamme) AS NomGamme, g.TpsGamme AS TempsTotalGamme, g.NbrOperations,
    l.Quantite AS QuantiteRealisee, l.Temps AS TempsRealise, l.LibTaille AS Taille,
    l.NumTicket, l.Majoration,
    SUM(l.Quantite) OVER (PARTITION BY l.IDOFabrication) AS QuantiteLectureCumulOF,
    CASE WHEN of2.Quantite > 0
         THEN ROUND(SUM(l.Quantite) OVER (PARTITION BY l.IDOFabrication) / NULLIF(of2.Quantite, 0) * 100, 2)
         ELSE NULL END AS RendementOFPct,
    l.SaisiPar, l.SaisiLe
FROM lectures l
INNER JOIN employe e ON l.IDEmploye = e.IDEmploye AND l.IDEmploye > 0
INNER JOIN chainemontage cm ON l.IDChaineMontage = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication AND l.IDOFabrication > 0
INNER JOIN operation op ON l.IDOperation = op.IDOperation AND l.IDOperation > 0
INNER JOIN gamme g ON l.IDGamme = g.IDGamme AND l.IDGamme > 0
WHERE l.Date > '2025-01-01';

ALTER TABLE vw_rh_production
    ADD PRIMARY KEY (IDLectures),
    ADD INDEX idx_emp_date (IDEmploye, DateLecture),
    ADD INDEX idx_of (IDOFabrication);