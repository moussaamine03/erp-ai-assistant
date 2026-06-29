-- ============================================================
-- BESOIN MÉTIER : RH / Production — 4 vues spécialisées
-- Données filtrées : Date > 2025-01-01
-- ============================================================


-- ============================================================
-- VUE 1 : vw_rh_employe
-- Focus : performance et production par employé
-- Agrégation par employé + date
-- ============================================================

SET NAMES utf8mb4;
CREATE OR REPLACE VIEW vw_rh_employe AS
WITH of_par_jour AS (
    -- OF distincts par employé et par jour → somme de leurs quantités
    SELECT
        l.IDEmploye,
        l.Date,
        SUM(of2.Quantite)   AS TotalQuantiteOF
    FROM (
        SELECT DISTINCT IDEmploye, Date, IDOFabrication
        FROM lectures
        WHERE Date > '2025-01-01'
          AND IDOFabrication > 0
    ) l
    INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication
    GROUP BY l.IDEmploye, l.Date
)
SELECT
    l.IDEmploye,
    CONCAT(TRIM(e.Nom), ' ', TRIM(e.Prenom))   AS NomCompletEmploye,
    TRIM(e.Nom)                                 AS NomEmploye,
    TRIM(e.Prenom)                              AS PrenomEmploye,
    e.Matricule,
    e.Specialite,
    CASE e.Sexe
        WHEN 1 THEN 'Homme'
        WHEN 2 THEN 'Femme'
        ELSE 'Non défini'
    END                                         AS Sexe,
    CASE e.Etat
        WHEN 1 THEN 'Actif'
        ELSE 'Inactif'
    END                                         AS EtatEmploye,
    e.TauxHoraire,
    e.DateEmbauche,
    -- Chaîne
    TRIM(cm.ChaineMontage)                      AS NomChaine,
    cm.Code                                     AS CodeChaine,
    -- Date et période
    l.Date                                      AS DateLecture,
    YEAR(l.Date)                                AS Annee,
    MONTH(l.Date)                               AS Mois,
    WEEK(l.Date)                                AS Semaine,
    -- Production
    SUM(l.Quantite)                             AS TotalPiecesJour,
    COUNT(l.IDLectures)                         AS NbrLectures,
    ROUND(SUM(l.Temps), 2)                      AS TempsTotal,
    -- Quantité OF du jour (OF distincts travaillés ce jour par cet employé)
    oj.TotalQuantiteOF                          AS TotalQuantiteOF,
    -- Rendement journalier = TotalPiecesJour / TotalQuantiteOF * 100
    CASE
        WHEN oj.TotalQuantiteOF > 0
        THEN ROUND(SUM(l.Quantite) / NULLIF(oj.TotalQuantiteOF, 0) * 100, 2)
        ELSE NULL
    END                                         AS RendementPct
FROM lectures l
INNER JOIN employe e         ON l.IDEmploye       = e.IDEmploye AND l.IDEmploye > 0
INNER JOIN chainemontage cm  ON l.IDChaineMontage  = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN operation op      ON l.IDOperation      = op.IDOperation AND l.IDOperation > 0
INNER JOIN of_par_jour oj    ON l.IDEmploye        = oj.IDEmploye AND l.Date = oj.Date
WHERE l.Date > '2025-01-01'
GROUP BY
    l.IDEmploye, e.Nom, e.Prenom, e.Matricule, e.Specialite,
    e.Sexe, e.Etat, e.TauxHoraire, e.DateEmbauche,
    cm.ChaineMontage, cm.Code,
    l.Date,
    oj.TotalQuantiteOF;


-- ============================================================
-- VUE 2 : vw_rh_chaine
-- Focus : production et charge par chaîne de montage
-- Agrégation par chaîne + date
-- ============================================================
CREATE OR REPLACE VIEW vw_rh_chaine AS
WITH of_par_jour_chaine AS (
    SELECT
        l.IDChaineMontage,
        l.Date,
        SUM(of2.Quantite)   AS TotalQuantiteOF
    FROM (
        SELECT DISTINCT IDChaineMontage, Date, IDOFabrication
        FROM lectures
        WHERE Date > '2025-01-01'
          AND IDOFabrication > 0
    ) l
    INNER JOIN ofabrication of2 ON l.IDOFabrication = of2.IDOFabrication
    GROUP BY l.IDChaineMontage, l.Date
)
SELECT
    l.IDChaineMontage,
    TRIM(cm.ChaineMontage)                      AS NomChaine,
    cm.Code                                     AS CodeChaine,
    -- Date et période
    l.Date                                      AS DateLecture,
    YEAR(l.Date)                                AS Annee,
    MONTH(l.Date)                               AS Mois,
    WEEK(l.Date)                                AS Semaine,
    -- OF en cours sur la chaîne
    TRIM(of2.OFAbrication)                      AS NumeroOF,
    CASE of2.Etat
        WHEN 0 THEN 'En cours'
        WHEN 1 THEN 'Terminé'
        WHEN 2 THEN 'Annulé'
        ELSE 'Inconnu'
    END                                         AS EtatOF,
    -- Production
    COUNT(DISTINCT l.IDEmploye)                 AS NbrEmployes,
    SUM(l.Quantite)                             AS TotalPiecesJour,
    COUNT(l.IDLectures)                         AS NbrLectures,
    ROUND(SUM(l.Temps), 2)                      AS TempsTotal,
    -- Quantité OF du jour pour cette chaîne
    oj.TotalQuantiteOF                          AS TotalQuantiteOF,
    -- Rendement journalier chaîne = TotalPiecesJour / TotalQuantiteOF * 100
    CASE
        WHEN oj.TotalQuantiteOF > 0
        THEN ROUND(SUM(l.Quantite) / NULLIF(oj.TotalQuantiteOF, 0) * 100, 2)
        ELSE NULL
    END                                         AS RendementPct
FROM lectures l
INNER JOIN chainemontage cm  ON l.IDChaineMontage = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN ofabrication of2  ON l.IDOFabrication  = of2.IDOFabrication AND l.IDOFabrication > 0
INNER JOIN operation op      ON l.IDOperation     = op.IDOperation AND l.IDOperation > 0
INNER JOIN of_par_jour_chaine oj ON l.IDChaineMontage = oj.IDChaineMontage AND l.Date = oj.Date
WHERE l.Date > '2025-01-01'
GROUP BY
    l.IDChaineMontage, cm.ChaineMontage, cm.Code,
    l.Date, of2.OFAbrication, of2.Etat,
    oj.TotalQuantiteOF;

-- ============================================================
-- VUE 3 : vw_rh_of
-- Focus : avancement et production par OF et opération
-- Agrégation par OF + opération
-- ============================================================

CREATE OR REPLACE VIEW vw_rh_of AS
SELECT
    l.IDOFabrication,
    TRIM(of2.OFAbrication)                      AS NumeroOF,
    of2.DtDebut                                 AS DateDebutOF,
    of2.DtFin                                   AS DateFinOF,
    of2.Quantite                                AS QuantitePrevueOF,
    of2.QtteLct                                 AS QuantiteLanceeOF,
    CASE of2.Etat
        WHEN 0 THEN 'En cours'
        WHEN 1 THEN 'Terminé'
        WHEN 2 THEN 'Annulé'
        ELSE 'Inconnu'
    END                                         AS EtatOF,
    -- Chaîne
    TRIM(cm.ChaineMontage)                      AS NomChaine,
    -- Opération
    l.IDOperation,
    TRIM(op.Operation)                          AS NomOperation,
    op.Code                                     AS CodeOperation,
    op.Temps                                    AS TempsPrevuOperation,
    -- Gamme
    TRIM(g.Gamme)                               AS NomGamme,
    g.TpsGamme                                  AS TempsTotalGamme,
    -- Production par opération
    COUNT(DISTINCT l.IDEmploye)                 AS NbrEmployes,
    SUM(l.Quantite)                             AS TotalPiecesOperation,
    ROUND(SUM(l.Temps), 2)                      AS TempsTotalRealise,
    -- Période
    MIN(l.Date)                                 AS PremiereLecture,
    MAX(l.Date)                                 AS DerniereLecture
FROM lectures l
INNER JOIN chainemontage cm  ON l.IDChaineMontage = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN ofabrication of2  ON l.IDOFabrication  = of2.IDOFabrication AND l.IDOFabrication > 0
INNER JOIN operation op      ON l.IDOperation     = op.IDOperation AND l.IDOperation > 0
INNER JOIN gamme g           ON l.IDGamme         = g.IDGamme AND l.IDGamme > 0
WHERE l.Date > '2025-01-01'
  AND l.IDOFabrication > 0
GROUP BY
    l.IDOFabrication, of2.OFAbrication, of2.DtDebut, of2.DtFin,
    of2.Quantite, of2.QtteLct, of2.Etat,
    cm.ChaineMontage,
    l.IDOperation, op.Operation, op.Code, op.Temps,
    g.Gamme, g.TpsGamme;

-- ============================================================
-- VUE 4 : vw_rh_production (vue globale détaillée existante)
-- Focus : détail ligne par ligne
-- ============================================================
CREATE OR REPLACE VIEW vw_rh_production AS
SELECT
    l.IDLectures,
    l.Date                                      AS DateLecture,
    YEAR(l.Date)                                AS Annee,
    MONTH(l.Date)                               AS Mois,
    WEEK(l.Date)                                AS Semaine,
    -- Employé
    l.IDEmploye,
    CONCAT(TRIM(e.Nom), ' ', TRIM(e.Prenom))    AS NomCompletEmploye,
    TRIM(e.Nom)                                 AS NomEmploye,
    TRIM(e.Prenom)                              AS PrenomEmploye,
    e.Matricule,
    e.Specialite,
    CASE e.Sexe
        WHEN 1 THEN 'Homme'
        WHEN 2 THEN 'Femme'
        ELSE 'Non défini'
    END                                         AS Sexe,
    CASE e.Etat
        WHEN 1 THEN 'Actif'
        ELSE 'Inactif'
    END                                         AS EtatEmploye,
    e.TauxHoraire,
    e.DateEmbauche,
    -- Chaîne
    l.IDChaineMontage,
    TRIM(cm.ChaineMontage)                      AS NomChaine,
    cm.Code                                     AS CodeChaine,
    -- OF
    l.IDOFabrication,
    TRIM(of2.OFAbrication)                      AS NumeroOF,
    of2.DtDebut                                 AS DateDebutOF,
    of2.DtFin                                   AS DateFinOF,
    of2.Quantite                                AS QuantiteOF,
    CASE of2.Etat
        WHEN 0 THEN 'En cours'
        WHEN 1 THEN 'Terminé'
        WHEN 2 THEN 'Annulé'
        ELSE 'Inconnu'
    END                                         AS EtatOF,
    -- Opération
    l.IDOperation,
    TRIM(op.Operation)                          AS NomOperation,
    op.Code                                     AS CodeOperation,
    op.Temps                                    AS TempsPrevuOperation,
    -- Gamme
    l.IDGamme,
    TRIM(g.Gamme)                                AS NomGamme,
    g.TpsGamme                                  AS TempsTotalGamme,
    g.NbrOperations,
    -- Lecture
    l.Quantite                                  AS QuantiteRealisee,
    l.Temps                                     AS TempsRealise,
    l.LibTaille                                 AS Taille,
    l.NumTicket,
    l.Majoration,
    -- Quantité cumulée des lectures pour l'OF (répétée sur chaque ligne)
    SUM(l.Quantite) OVER (PARTITION BY l.IDOFabrication)
                                                 AS QuantiteLectureCumulOF,
    -- Rendement OF = (Somme Quantite lectures de l'OF / Quantite OF) * 100
    CASE
        WHEN of2.Quantite > 0
        THEN ROUND(
            SUM(l.Quantite) OVER (PARTITION BY l.IDOFabrication)
            / NULLIF(of2.Quantite, 0) * 100
        , 2)
        ELSE NULL
    END                                         AS RendementOFPct,
    l.SaisiPar,
    l.SaisiLe
FROM lectures l
INNER JOIN employe e          ON l.IDEmploye       = e.IDEmploye AND l.IDEmploye > 0
INNER JOIN chainemontage cm   ON l.IDChaineMontage  = cm.IDChaineMontage AND l.IDChaineMontage > 0
INNER JOIN ofabrication of2   ON l.IDOFabrication   = of2.IDOFabrication AND l.IDOFabrication > 0
INNER JOIN operation op       ON l.IDOperation      = op.IDOperation AND l.IDOperation > 0
INNER JOIN gamme g            ON l.IDGamme          = g.IDGamme AND l.IDGamme > 0
WHERE l.Date > '2025-01-01';
