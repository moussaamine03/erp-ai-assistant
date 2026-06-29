-- ============================================================
-- BESOIN MÉTIER : Achat
-- Tables sources : achat, ligneachat, fournisseur, mp
-- Liaisons :
--   achat.IDFournisseur → fournisseur.IDFournisseur
--   ligneachat.IDAchat  → achat.IDAchat
--   ligneachat.IDMP     → mp.IDMP
-- ============================================================

-- ============================================================
-- VUE 1 : vw_achat
-- Vue complète joignant achat + ligneachat + fournisseur + mp
-- Une ligne = une ligne d'achat avec toutes ses informations
-- ============================================================
SET NAMES utf8mb4;
CREATE OR REPLACE VIEW vw_achat AS
SELECT
    -- Entête achat
    a.IDAchat,
    a.LibAchat                                          AS NumeroAchat,
    a.Facture                                           AS NumeroFactureFournisseur,
    a.Date                                              AS DateAchat,
    a.DateFacture                                       AS DateFactureFournisseur,
    a.DateEcheance,
    -- Fournisseur
    a.IDFournisseur,
    TRIM(a.Fournisseur)                                 AS NomFournisseur,
    f.Adresse                                           AS AdresseFournisseur,
    f.Pays                                              AS PaysFournisseur,
    f.Tel                                               AS TelFournisseur,
    -- Montants entête
    a.TotalHT,
    a.TotalTVA,
    a.TotalTTC,
    a.TotalFodec,
    a.Remise                                            AS RemiseAchat,
    a.Timbre,
    a.ResteReglemnt                                     AS ResteARegler,
    -- Statut règlement
    CASE a.EtatReglement
        WHEN 0 THEN 'Non réglé'
        WHEN 1 THEN 'Partiellement réglé'
        WHEN 2 THEN 'Totalement réglé'
    END                                                 AS StatutReglement,
    -- Type achat
    CASE a.Type
        WHEN 0 THEN 'Achat normal'
        WHEN 1 THEN 'Avoir'
        WHEN 2 THEN 'Proforma'
    END                                                 AS TypeAchat,
    CASE a.Etat
        WHEN 1 THEN 'Actif'
        ELSE 'Inactif'
    END                                                 AS EtatAchat,
    -- Quantité totale
    a.TotalQtte,
    -- Ligne achat
    la.IDLigneAchat,
    la.IDMP,
    la.CodeMP,
    la.LibMP                                            AS DesignationMP,
    la.Quantite,
    la.Prix                                             AS PrixUnitaire,
    ROUND(la.Quantite * la.Prix, 3)                     AS MontantLigneHT,
    la.Remise                                           AS RemiseLigne,
    la.TauxTVA,
    la.TauxFODEC,
    la.MntFODEC,
    la.Epaisseur,
    la.LibBL,
    -- Matière première
    mp.Description                                      AS DescriptionMP,
    mp.Couleur                                          AS CouleurMP,
    mp.Matiere                                          AS TypeMatiere,
    mp.Composition                                      AS CompositionMP,
    mp.Unite                                            AS UniteMP,
    mp.StockMin,
    mp.StockAlerte,
    -- Traçabilité
    a.SaisiPar,
    a.SaisiLe,
    a.ModifiePar,
    a.ModifieLe,
    a.Observations,
    -- Période
    a.Annee                                             AS AnneeAchat,
    MONTH(a.Date)                                       AS MoisAchat
FROM achat a
INNER JOIN ligneachat la ON a.IDAchat       = la.IDAchat
INNER JOIN fournisseur f  ON a.IDFournisseur = f.IDFournisseur
INNER JOIN  mp             ON la.IDMP         = mp.IDMP;


-- ============================================================
-- VUE 2 : vw_achat_entetes
-- Vue allégée sans les lignes de détail — une ligne = un achat
-- ============================================================
CREATE OR REPLACE VIEW vw_achat_entetes AS
SELECT
    a.IDAchat,
    a.LibAchat                                          AS NumeroAchat,
    a.Facture                                           AS NumeroFactureFournisseur,
    a.Date                                              AS DateAchat,
    a.DateFacture                                       AS DateFactureFournisseur,
    a.DateEcheance,
    a.IDFournisseur,
    TRIM(a.Fournisseur)                                 AS NomFournisseur,
    f.Pays                                              AS PaysFournisseur,
    a.TotalHT,
    a.TotalTVA,
    a.TotalTTC,
    a.TotalFodec,
    a.Remise                                            AS RemiseAchat,
    a.ResteReglemnt                                     AS ResteARegler,
    a.TotalQtte,
    CASE a.EtatReglement
        WHEN 0 THEN 'Non réglé'
        WHEN 1 THEN 'Partiellement réglé'
        WHEN 2 THEN 'Totalement réglé'
    END                                                 AS StatutReglement,
    CASE a.Type
        WHEN 0 THEN 'Achat normal'
        WHEN 1 THEN 'Avoir'
        WHEN 2 THEN 'Proforma'
    END                                                 AS TypeAchat,
    CASE a.Etat
        WHEN 1 THEN 'Actif'
        ELSE 'Inactif'
    END                                                 AS EtatAchat,
    a.SaisiPar,
    a.SaisiLe,
    a.Annee                                             AS AnneeAchat,
    MONTH(a.Date)                                       AS MoisAchat
FROM achat a
INNER JOIN fournisseur f ON a.IDFournisseur = f.IDFournisseur;


-- ============================================================
-- VUE 3 : vw_achat_kpi_fournisseur
-- KPI achats agrégés par fournisseur
-- ============================================================
CREATE OR REPLACE VIEW vw_achat_kpi_fournisseur AS
SELECT
    a.IDFournisseur,
    TRIM(f.Fournisseur)                                 AS NomFournisseur,
    f.Pays                                              AS PaysFournisseur,
    COUNT(DISTINCT a.IDAchat)                           AS NombreAchats,
    ROUND(SUM(a.TotalHT), 3)                            AS TotalAchatsHT,
    ROUND(SUM(a.TotalTTC), 3)                           AS TotalAchatsTTC,
    ROUND(SUM(a.ResteReglemnt), 3)                      AS TotalResteARegler,
    ROUND(AVG(a.TotalHT), 3)                            AS MoyenneAchatHT,
    SUM(CASE a.EtatReglement WHEN 2 THEN 1 ELSE 0 END)  AS NbAchatsReglés,
    SUM(CASE a.EtatReglement WHEN 0 THEN 1 ELSE 0 END)  AS NbAchatsNonReglés,
    MIN(a.Date)                                         AS PremierAchat,
    MAX(a.Date)                                         AS DernierAchat
FROM achat a
INNER JOIN fournisseur f ON a.IDFournisseur = f.IDFournisseur
GROUP BY a.IDFournisseur, f.Fournisseur, f.Pays;
