-- ============================================================
-- BESOIN MÉTIER : Article (v2 - INNER JOIN corrigé)
-- ============================================================

-- ============================================================
-- VUE 1 : vw_article
-- Vue complète article avec INNER JOIN sur couleur, famille, grille
-- LEFT JOIN uniquement pour client et fournisseur (optionnels)
-- ============================================================
SET NAMES utf8mb4;
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


-- ============================================================
-- VUE 2 : vw_article_tailles
-- Vue articles avec leurs tailles disponibles
-- INNER JOIN sur couleur, famille, grille, tailles
-- ============================================================
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

-- ============================================================
-- VUE 3 : vw_article_kpi_famille
-- KPI articles agrégés par famille
-- ============================================================
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
