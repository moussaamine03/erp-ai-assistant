-- ============================================================
-- SCRIPT DE (RE)CREATION DES VUES METIER
-- A exécuter à chaque lancement du projet.
--
-- Contient les besoins métier : Facturation, Article, Achat.
-- (Le besoin RH/Production n'est PAS ici : il est matérialisé en
--  tables physiques, rafraîchies 1x/jour — voir
--  rh_production_tables.sql + rh_refresh_worker.py)
--
-- Toutes les définitions utilisent CREATE OR REPLACE VIEW : ce
-- script est donc idempotent, il peut être rejoué sans risque à
-- chaque démarrage (aucune donnée n'est stockée dans une vue).
--
-- ORDRE IMPORTANT : vw_facturation et vw_article doivent être
-- créées AVANT vw_facturation_detail_article, qui dépend des deux.
-- ============================================================

SET NAMES utf8mb4;

-- ============================================================
-- BESOIN MÉTIER : Facturation
-- Tables sources : facture, lignefac
-- ============================================================

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


-- ============================================================
-- BESOIN MÉTIER : Article (v2 - INNER JOIN corrigé)
-- Tables sources : article, ar_couleur, arfamille, grille, client, tailles
-- ============================================================

CREATE OR REPLACE VIEW vw_article AS
SELECT
    a.IDArticle,
    a.Code                                          AS CodeArticle,
    a.Article                                       AS DesignationArticle,
    a.Reference,
    -- Couleur (INNER JOIN : articles sans couleur valide exclus)
    c.Couleur                                       AS NomCouleur,
    c.Code                                          AS CodeCouleur,
    -- Famille (INNER JOIN : articles sans famille valide exclus)
    f.Famille                                       AS NomFamille,
    f.Code                                          AS CodeFamille,
    -- Grille de tailles (INNER JOIN : articles sans grille valide exclus)
    g.Grille                                        AS NomGrille,
    -- Client associé (LEFT JOIN : optionnel)
    cl.Client                                       AS NomClient,
    -- Prix et valeurs
    a.Prix                                          AS PrixVente,
    a.PrixFac                                       AS PrixFacturation,
    a.prixMP                                        AS PrixMatieresPremieres,
    a.ValeurTissu,
    a.ValeurFourniture,
    a.ValeurMP                                      AS ValeurTotalMP,
    a.PrixEmballage,
    a.TauxTVA,
    -- Caractéristiques physiques
    a.PoidsBrut,
    a.PoidsNet,
    a.Composition,
    a.CodeDouane,
    a.Dimensions,
    -- Production
    a.Cadence,
    a.TempsClient,
    a.TempsAtelier,
    a.TempsFinitions,
    a.TempsUnitaire,
    a.NbrPiecesColis,
    a.NbrColisPalette,
    -- Stock
    a.StockMin,
    a.StockAlerte,
    -- Type et état
    CASE a.Etat WHEN 1 THEN 'Actif' ELSE 'Inactif' END  AS EtatArticle,
    CASE a.SemiFini WHEN 1 THEN 'Semi-fini' ELSE 'Produit fini' END AS TypeProduit,
    CASE a.IsMP WHEN 1 THEN 'Matière première' ELSE 'Article' END AS NatureArticle,
    a.NomenclatureValide,
    -- Traçabilité
    a.SaisiPar,
    a.SaisiLe,
    a.ModifiePar,
    a.ModifieLe,
    a.Observations
FROM article a
INNER JOIN ar_couleur c   ON a.IDAr_Couleur  = c.IDAr_Couleur
INNER JOIN arfamille f    ON a.IDArFamille   = f.IDArFamille
INNER JOIN grille g       ON a.IDGrille      = g.IDGrille
INNER JOIN  client cl      ON a.IDClient      = cl.IDClient;


CREATE OR REPLACE VIEW vw_article_tailles AS
SELECT
    a.IDArticle,
    a.Code                                          AS CodeArticle,
    a.Article                                       AS DesignationArticle,
    f.Famille                                       AS NomFamille,
    c.Couleur                                       AS NomCouleur,
    g.Grille                                        AS NomGrille,
    g.IDGrille,
    t.IdTaille,
    t.LibTaille                                     AS Taille,
    t.Ordre                                         AS OrdreTaille,
    CASE a.Etat WHEN 1 THEN 'Actif' ELSE 'Inactif' END AS EtatArticle
FROM article a
INNER JOIN ar_couleur c ON a.IDAr_Couleur = c.IDAr_Couleur
INNER JOIN arfamille f  ON a.IDArFamille  = f.IDArFamille
INNER JOIN grille g     ON a.IDGrille     = g.IDGrille
INNER JOIN tailles t    ON g.IDGrille     = t.IDGrille
ORDER BY a.IDArticle, t.Ordre;


CREATE OR REPLACE VIEW vw_article_kpi_famille AS
SELECT
    f.IDArFamille,
    f.Famille                                       AS NomFamille,
    COUNT(a.IDArticle)                              AS NombreArticles,
    SUM(CASE a.Etat WHEN 1 THEN 1 ELSE 0 END)      AS ArticlesActifs,
    SUM(CASE a.Etat WHEN 0 THEN 1 ELSE 0 END)      AS ArticlesInactifs,
    ROUND(AVG(a.Prix), 3)                           AS PrixMoyen,
    ROUND(MIN(a.Prix), 3)                           AS PrixMin,
    ROUND(MAX(a.Prix), 3)                           AS PrixMax,
    ROUND(AVG(a.Cadence), 2)                        AS CadenceMoyenne,
    ROUND(AVG(a.TempsClient), 2)                    AS TempsMoyenClient,
    COUNT(DISTINCT a.IDAr_Couleur)                  AS NombreCouleurs,
    COUNT(DISTINCT a.IDClient)                      AS NombreClients
FROM arfamille f
LEFT JOIN article a ON f.IDArFamille = a.IDArFamille
GROUP BY f.IDArFamille, f.Famille;


-- ============================================================
-- BESOIN MÉTIER : Achat
-- Tables sources : achat, ligneachat, fournisseur, mp
-- ============================================================

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
GROUP BY a.IDFournisseur, f.Pays, f.Fournisseur;


-- ============================================================
-- BESOIN MÉTIER : Facturation + Article (jointure ciblée)
-- Dépend de vw_facturation et vw_article, créées ci-dessus.
-- ============================================================

CREATE OR REPLACE VIEW vw_facturation_detail_article AS
SELECT
    -- Infos facture
    f.IDFacture,
    f.NumeroFacture,
    f.DateFacture,
    f.NomClient,
    f.IDClient,
    f.TypeFacture,
    f.StatutReglement,
    f.StatutAcquittement,
    f.AnneeFacture,
    f.MoisFacture,
    -- Infos ligne facture
    f.IDLigneFac,
    f.IDArticle,
    f.CodeArticle,
    f.DesignationProduit,
    f.Quantite,
    f.PrixVente,
    f.MontantLigneHT,
    f.TauxTVA,
    f.RemiseLigne,
    f.LibBL,
    -- Infos article enrichies
    a.NomCouleur,
    a.NomFamille,
    a.NomGrille,
    a.Composition,
    a.CodeDouane,
    a.PoidsBrut                AS PoidsArticle,
    a.Cadence,
    a.ValeurTissu,
    a.ValeurFourniture,
    a.ValeurTotalMP,
    a.TypeProduit,
    a.NatureArticle
FROM vw_facturation f
INNER JOIN vw_article a ON f.IDArticle = a.IDArticle
ORDER BY f.IDArticle, f.IDFacture, f.IDLigneFac;