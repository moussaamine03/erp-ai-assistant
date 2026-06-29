-- ============================================================
-- BESOIN MÉTIER : Facturation + Article (jointure ciblée)
-- Vue : vw_facturation_detail_article
-- Répond aux questions croisant facturation et articles
-- ============================================================
SET NAMES utf8mb4;
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