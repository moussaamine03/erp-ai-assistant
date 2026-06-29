-- ============================================================
--  VUE MÉTIER : vw_facturation
--  Besoin     : Facturation (MVP - AI Production Planning Assistant)
--  Tables     : facture + lignefac
--  Accès      : LECTURE SEULE — aucun DELETE / UPDATE autorisé
--  Créée le   : 2026-06-04
-- ============================================================
SET NAMES utf8mb4;
CREATE OR REPLACE VIEW vw_facturation AS
SELECT
    -- ── Entête facture ──────────────────────────────────────
    f.IDFacture,
    f.LibFacture                                    AS NumeroFacture,
    f.DateFacture,
    f.Client                                        AS NomClient,
    f.IDClient,
    f.Adresse                                       AS AdresseClient,
    f.MF                                            AS MatriculeFiscal,

    -- ── Montants ────────────────────────────────────────────
    f.TotalHT,
    f.TotalTVA,
    f.TotalTTC,
    f.Remise                                        AS RemiseFacture,
    f.Timbre,
    f.TotalFodec,

    -- ── Statut / règlement ──────────────────────────────────
    CASE f.Acquittée
        WHEN 1 THEN 'Acquittée'
        ELSE        'Non acquittée'
    END                                             AS StatutAcquittement,

    CASE f.EtatReglement
        WHEN 0 THEN 'Non réglée'
        WHEN 1 THEN 'Partiellement réglée'
        WHEN 2 THEN 'Totalement réglée'
        ELSE        'Inconnu'
    END                                             AS StatutReglement,

    f.ResteReglemnt                                 AS ResteARegler,
    f.ModeRèglement,
    f.ConditionReglement,

    -- ── Type / catégorie ────────────────────────────────────
    CASE f.Type
        WHEN 0 THEN 'Facture normale'
        WHEN 1 THEN 'Avoir'
        WHEN 2 THEN 'Proforma'
        WHEN 3 THEN 'Facture complémentaire'
        ELSE        'Autre'
    END                                             AS TypeFacture,

    f.IDCategorieFacture,

    -- ── Transport / export ──────────────────────────────────
    f.Transporteur,
    f.PoidsBrut,
    f.PoidsNet,
    f.Volume,
    f.NbrColis,

    -- ── Traçabilité ─────────────────────────────────────────
    f.SaisiPar,
    f.SaisiLe,
    f.ModifiePar,
    f.ModifieLe,
    f.Observations,

    -- ── Lignes de facture ────────────────────────────────────
    lf.IDLigneFac,
    lf.IDArticle,
    lf.Code                                         AS CodeArticle,
    lf.LibProd                                      AS DesignationProduit,
    lf.Quantité                                     AS Quantite,
    lf.Quantite2,
    lf.PrixVente,
    lf.Remise                                       AS RemiseLigne,
    lf.TauxTVA,
    lf.TauxFODEC,
    lf.MntFODEC,
    lf.PoidsBrut                                    AS PoidsLigne,
    lf.PoidsNet                                     AS PoidsNetLigne,
    lf.ValeurTissu,
    lf.ValeurFourniture,
    lf.ValeurMP,
    lf.Majoration,
    lf.LibBL,
    lf.Composition,
    lf.CodeDouane,
    lf.Observations                                 AS ObservationsLigne,

    -- ── Colonnes calculées utiles ───────────────────────────
    ROUND(lf.Quantité * lf.PrixVente, 3)            AS MontantLigneHT,
    ROUND(lf.Quantité * lf.PrixVente
          * (1 - lf.Remise / 100), 3)               AS MontantLigneApresRemise,
    YEAR(f.DateFacture)                             AS AnneeFacture,
    MONTH(f.DateFacture)                            AS MoisFacture

FROM facture f
LEFT JOIN lignefac lf ON lf.IDFacture = f.IDFacture;


-- ============================================================
--  VUES COMPLÉMENTAIRES LÉGÈRES (résumés métier)
-- ============================================================

-- Résumé par facture (sans le détail des lignes)
CREATE OR REPLACE VIEW vw_facturation_entetes AS
SELECT
    f.IDFacture,
    f.LibFacture                                    AS NumeroFacture,
    f.DateFacture,
    f.Client                                        AS NomClient,
    f.IDClient,
    f.MF                                            AS MatriculeFiscal,
    f.TotalHT,
    f.TotalTTC,
    f.ResteReglemnt                                 AS ResteARegler,
    CASE f.Acquittée
        WHEN 1 THEN 'Acquittée'
        ELSE        'Non acquittée'
    END                                             AS StatutAcquittement,
    CASE f.EtatReglement
        WHEN 0 THEN 'Non réglée'
        WHEN 1 THEN 'Partiellement réglée'
        WHEN 2 THEN 'Totalement réglée'
        ELSE        'Inconnu'
    END                                             AS StatutReglement,
    CASE f.Type
        WHEN 0 THEN 'Facture normale'
        WHEN 1 THEN 'Avoir'
        WHEN 2 THEN 'Proforma'
        WHEN 3 THEN 'Facture complémentaire'
        ELSE        'Autre'
    END                                             AS TypeFacture,
    f.ModeRèglement,
    f.ConditionReglement,
    f.SaisiPar,
    f.SaisiLe,
    f.Transporteur,
    YEAR(f.DateFacture)                             AS AnneeFacture,
    MONTH(f.DateFacture)                            AS MoisFacture
FROM facture f;


-- Résumé KPI par client
CREATE OR REPLACE VIEW vw_facturation_kpi_client AS
SELECT
    f.IDClient,
    f.Client                                        AS NomClient,
    COUNT(DISTINCT f.IDFacture)                     AS NombreFactures,
    SUM(f.TotalHT)                                  AS ChiffreAffairesHT,
    SUM(f.TotalTTC)                                 AS ChiffreAffairesTTC,
    SUM(f.ResteReglemnt)                            AS TotalResteARegler,
    SUM(CASE WHEN f.Acquittée = 1 THEN 1 ELSE 0 END) AS NbFacturesAcquittees,
    SUM(CASE WHEN f.Acquittée = 0 THEN 1 ELSE 0 END) AS NbFacturesNonAcquittees,
    MIN(f.DateFacture)                              AS PremiereFacture,
    MAX(f.DateFacture)                              AS DerniereFacture
FROM facture f
GROUP BY f.IDClient, f.Client;
