"""Data cleaning pipeline — Kpankpanu survey (base_femmes_2024.xlsx).

EN: Assertion-driven cleaning producing an ML-ready dataset from the raw KoboToolbox
export (106 rows x 138 columns). Only the 9 target variables requested are retained,
plus the derived indicators explicitly validated with the user.
FR: Pipeline de nettoyage piloté par des assertions produisant un jeu de données prêt
pour le ML à partir de l'export brut KoboToolbox (106 lignes x 138 colonnes). Seules
les 9 variables cibles demandées sont conservées, avec les indicateurs dérivés validés
auprès de l'utilisateur.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RANDOM_SEED = 42

# EN: Resolve paths relative to the project root (src/cleaning.py -> ..)
# FR: Résout les chemins relatifs à la racine du projet (src/cleaning.py -> ..)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_PATH = PROJECT_ROOT / "data" / "raw" / "base_femmes_2024.xlsx"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_PATH = PROCESSED_DIR / "base_femmes_2024_clean.csv"

# Raw KoboToolbox column name -> English variable name.
# Keys are stripped of trailing whitespace to match Kobo exports robustly.
RAW_COLUMNS: dict[str, str] = {
    "Quel est votre âge ?": "age",
    "A combien s'élève votre revenu mensuel (FCFA) ?": "income",
    "A combien s'élève le revenu moyen mensuel de votre ménage (FCFA) ?": "household_income",
    "Quel est votre niveau d'instruction ?": "education",
    "Êtes-vous actuellement enceinte ?": "is_pregnant",
    "Avez-vous au moins un enfant âgé de 0 à 5 ans révolu ?": "has_child_under_5",
    "Combien d'enfant avez-vous ?": "num_children",
    "Seriez-vous intéressée à consommer personnellement la farine Kpankpanu, étant donné qu'elle est également enrichie en fer et bénéfique pour les adultes ?": "buy_intent",
    "À quel prix seriez-vous prête à acheter un paquet de farine Kpankpanu de 1 kg (FCFA) ?": "ideal_price",
    'Pensez-vous que la farine enrichie "Kpankpanu" pourrait contribuer à la nutrition de vos enfants grâce à sa composition ?': "perceived_child_benefit",
}

YES_NO_MAP = {"oui": 1, "non": 0}


def strip_columns(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Strip leading/trailing whitespace from all column names.
    FR: Supprime les espaces en début/fin de tous les noms de colonnes."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def keep_target_columns(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Keep only the target variables listed in RAW_COLUMNS (plus _id for traceability).
    FR: Ne garde que les variables cibles listées dans RAW_COLUMNS (plus _id pour traçabilité)."""
    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    assert not missing, f"EN: Required raw columns missing: {missing}\nFR: Colonnes brutes requises manquantes : {missing}"
    keep_cols = ["_id"] + list(RAW_COLUMNS.keys())
    df = df[keep_cols].copy()
    assert df.shape[1] == len(keep_cols), "EN: Column selection failed\nFR: La sélection des colonnes a échoué"
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Rename raw French column names to English snake_case names.
    FR: Renomme les noms de colonnes bruts en français vers des noms snake_case en anglais."""
    df = df.rename(columns={"_id": "respondent_id", **RAW_COLUMNS})
    expected = ["respondent_id"] + list(RAW_COLUMNS.values())
    missing = [c for c in expected if c not in df.columns]
    assert not missing, f"EN: Renamed columns missing: {missing}\nFR: Colonnes renommées manquantes : {missing}"
    return df


def validate_structure(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Validate row count, duplicate rows and respondent id uniqueness.
    FR: Valide le nombre de lignes, les doublons de lignes et l'unicité des ids répondants."""
    assert len(df) == 106, f"EN: Expected 106 rows, got {len(df)}\nFR: 106 lignes attendues, {len(df)} trouvées"
    assert df["respondent_id"].is_unique, "EN: Duplicate respondent_id found\nFR: Doublons de respondent_id détectés"
    n_dup_rows = int(df.duplicated().sum())
    assert n_dup_rows == 0, f"EN: {n_dup_rows} duplicate rows found\nFR: {n_dup_rows} lignes en doublon détectées"
    return df


def encode_binary(df: pd.DataFrame, col: str, out_col: str) -> pd.DataFrame:
    """EN: Encode a Oui/Non column into 1/0. Keeps NaN untouched.
    FR: Encode une colonne Oui/Non en 1/0. Ne touche pas aux NaN."""
    s = df[col].astype(str).str.strip().str.lower()
    mapped = s.map(YES_NO_MAP).astype("Int64")
    valid_mask = s.isin(["oui", "non"])
    n_invalid = int((~valid_mask).sum())
    assert n_invalid == 0, f"EN: {n_invalid} non-binary values in {col}\nFR: {n_invalid} valeurs non binaires dans {col}"
    df[out_col] = mapped
    n_na = int(df[out_col].isna().sum())
    assert n_na == 0, f"EN: Unexpected NaN after binary encoding of {col}\nFR: NaN inattendu après encodage binaire de {col}"
    return df


def convert_targets(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Convert dichotomous targets (is_pregnant, has_child_under_5, buy_intent) to 1/0.
    FR: Convertit les cibles dichotomiques (is_pregnant, has_child_under_5, buy_intent) en 1/0."""
    df = encode_binary(df, "is_pregnant", "is_pregnant")
    df = encode_binary(df, "has_child_under_5", "has_child_under_5")
    df = encode_binary(df, "buy_intent", "buy_intent")
    # Perceived child benefit: 77 answered, 29 NaN (skip logic: no child < 5). Keep NaN.
    s = df["perceived_child_benefit"].astype(str).str.strip().str.lower()
    df["perceived_child_benefit"] = s.map(YES_NO_MAP).astype("Int64")
    n_na_pc = int(df["perceived_child_benefit"].isna().sum())
    n_na_hc = int(df["has_child_under_5"].eq(0).sum())
    assert n_na_pc == n_na_hc, (
        "EN: perceived_child_benefit NaN must match has_child_under_5 == 0 (skip logic)\n"
        f"FR: Les NaN de perceived_child_benefit doivent correspondre à has_child_under_5 == 0 (logique de saut Kobo)"
    )
    df["perceived_child_benefit_missing"] = df["perceived_child_benefit"].isna().astype("Int64")
    return df


def normalize_education(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Normalize education labels (accents/case) and cast to category.
    FR: Normalise les libellés de niveau d'instruction (accents/casse) et passe en catégorie."""
    df = df.copy()
    df["education"] = (
        df["education"].astype(str).str.strip()
        .replace({"Superieur": "Supérieur"})
        .replace({"Aucun": "Aucun"})
    )
    allowed = {"Aucun", "Primaire", "Secondaire", "Supérieur"}
    assert set(df["education"].dropna().unique()) <= allowed, (
        "EN: Unexpected education labels\nFR: Libellés de niveau d'instruction inattendus"
    )
    df["education"] = df["education"].astype("category")
    return df


def process_numeric_targets(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Process age, income, household_income, ideal_price with user-validated rules:
    - income / household_income: keep 0 as-is (financially dependent women at home).
    - ideal_price: correct obvious typo > 5000 by /10 (e.g. 15001 -> 1500); keep NaN.
    FR: Traitement des cibles numériques selon les règles validées avec l'utilisateur :
    - income / household_income : on garde 0 tel quel (femmes sans revenu personnel).
    - ideal_price : corrige l'erreur de frappe > 5000 par /10 (ex. 15001 -> 1500) ; on garde les NaN."""
    df = df.copy()

    # age: plausible range for the target population (pregnant women / mothers of < 5).
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
    n_age_na = int(df["age"].isna().sum())
    assert n_age_na == 0, f"EN: {n_age_na} missing age values\nFR: {n_age_na} valeurs d'âge manquantes"
    assert df["age"].min() >= 15 and df["age"].max() <= 60, (
        "EN: age outside plausible range [15, 60]\nFR: âge hors de l'intervalle plausible [15, 60]"
    )

    # income: keep 0 as-is, add dependency indicator.
    df["income"] = pd.to_numeric(df["income"], errors="coerce").astype("Int64")
    assert df["income"].isna().sum() == 0, "EN: Missing income values\nFR: Valeurs de revenu manquantes"
    df["is_financially_dependent"] = (df["income"] == 0).astype("Int64")

    # household_income: numeric as requested; keep 0 as-is (user-validated socio-economic reality).
    df["household_income"] = pd.to_numeric(df["household_income"], errors="coerce").astype("Int64")
    assert df["household_income"].isna().sum() == 0, "EN: Missing household income values\nFR: Valeurs de revenu ménage manquantes"

    # ideal_price: typo correction then keep NaN.
    df["ideal_price"] = pd.to_numeric(df["ideal_price"], errors="coerce")
    typo_mask = df["ideal_price"] > 5000
    n_typos = int(typo_mask.sum())
    if n_typos:
        corrected = df.loc[typo_mask, "ideal_price"] / 10
        assert ((corrected >= 100) & (corrected <= 2500)).all(), (
            "EN: Typo-corrected ideal_price out of plausible range\n"
            "FR: Valeurs de prix corrigées hors intervalle plausible"
        )
        df.loc[typo_mask, "ideal_price"] = corrected.values
    df["price_corrected"] = typo_mask.astype("Int64")
    assert ((df["ideal_price"] <= 5000) | df["ideal_price"].isna()).all(), (
        "EN: ideal_price still contains values > 5000\nFR: ideal_price contient encore des valeurs > 5000"
    )
    df["ideal_price_missing"] = df["ideal_price"].isna().astype("Int64")
    return df


def process_num_children(df: pd.DataFrame) -> pd.DataFrame:
    """EN: num_children: 29 NaN exactly match has_child_under_5 == 0 (Kobo skip logic).
    Cap the outlier value 15 to 5 (user-validated winsorization) and flag it.
    FR: num_children : les 29 NaN correspondent exactement à has_child_under_5 == 0 (logique de saut Kobo).
    Plafonne la valeur aberrante 15 à 5 (winsorisation validée) et la signale."""
    df = df.copy()
    structural_na = df["num_children"].isna()
    assert structural_na.eq(df["has_child_under_5"] == 0).all(), (
        "EN: num_children NaN must exactly match has_child_under_5 == 0 (skip logic)\n"
        "FR: Les NaN de num_children doivent correspondre exactement à has_child_under_5 == 0 (logique de saut)"
    )
    outlier_mask = df["num_children"] > 10
    n_outliers = int(outlier_mask.sum())
    assert n_outliers == 1, f"EN: Expected exactly 1 num_children outlier, got {n_outliers}\nFR: 1 valeur aberrante de num_children attendue, {n_outliers} trouvées"
    df.loc[outlier_mask, "num_children"] = 5
    df["num_children_outlier"] = outlier_mask.astype("Int64")
    df["num_children_missing"] = structural_na.astype("Int64")
    df["num_children"] = pd.to_numeric(df["num_children"], errors="coerce").astype("Int64")
    assert df["num_children"].max() <= 5, "EN: num_children still > 5 after capping\nFR: num_children encore > 5 après plafond"
    return df


def low_price_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Flag respondents stating an acceptable price <= 500 FCFA (user-validated).
    FR: Marque les répondants déclarant un prix acceptable <= 500 FCFA (validé avec l'utilisateur)."""
    df = df.copy()
    df["low_price_respondent"] = ((df["ideal_price"] <= 500) & df["ideal_price"].notna()).astype("Int64")
    return df


def population_check(df: pd.DataFrame) -> pd.DataFrame:
    """EN: All respondents must be pregnant and/or mothers of a child under 5.
    FR: Tous les répondants doivent être enceintes et/ou mères d'un enfant de moins de 5 ans."""
    in_pop = (df["is_pregnant"] == 1) | (df["has_child_under_5"] == 1)
    assert in_pop.all(), "EN: Rows outside target population detected\nFR: Lignes hors population cible détectées"
    return df

def impute_missing_prices(df: pd.DataFrame) -> pd.DataFrame:
    """EN: Impute missing ideal_price values with the median and flag the imputed rows.
    FR: Impute les valeurs manquantes de ideal_price par la médiane et marque les lignes imputées."""
    df = df.copy()
    
    # EN: Identify rows to impute BEFORE filling (to keep the traceability)
    # FR: Identifie les lignes à imputer AVANT de remplir (pour garder la traçabilité)
    impute_mask = df["ideal_price"].isna()
    
    # EN: Create a dedicated traceability flag for this specific operation
    # FR: Crée un indicateur de traçabilité dédié à cette opération spécifique
    df["ideal_price_imputed"] = impute_mask.astype("Int64")
    
    # EN: Impute with median
    # FR: Impute avec la médiane
    median_price = df["ideal_price"].median()
    df["ideal_price"] = df["ideal_price"].fillna(median_price)
    
    # EN: Assertions to verify the operation
    # FR: Assertions pour vérifier l'opération
    assert df["ideal_price"].isna().sum() == 0, "EN: Imputation failed\nFR: L'imputation a échoué"
    assert df["ideal_price_imputed"].sum() == impute_mask.sum(), "EN: Flag incoherence\nFR: Incohérence dans le flag"
    
    return df

def clean() -> pd.DataFrame:
    """EN: Run the full cleaning pipeline.
    FR: Exécute le pipeline complet de nettoyage."""
    df = pd.read_excel(RAW_PATH)
    assert df.shape == (106, 138), f"EN: Expected raw shape (106, 138), got {df.shape}\nFR: Forme brute attendue (106, 138), {df.shape} trouvée"

    df = strip_columns(df)
    df = keep_target_columns(df)
    df = rename_columns(df)
    df = validate_structure(df)
    df = convert_targets(df)
    df = normalize_education(df)
    df = process_numeric_targets(df)
    df = process_num_children(df)
    df = low_price_indicator(df)
    df = population_check(df)
    df = impute_missing_prices(df)

    # Final column ordering.
    ordered = [
        "respondent_id",
        "age",
        "income",
        "is_financially_dependent",
        "household_income",
        "education",
        "is_pregnant",
        "has_child_under_5",
        "num_children",
        "num_children_outlier",
        "num_children_missing",
        "ideal_price",
        "ideal_price_missing",
        "ideal_price_imputed",
        "price_corrected",
        "low_price_respondent",
        "buy_intent",
        "perceived_child_benefit",
        "perceived_child_benefit_missing",
    ]
    df = df[ordered]
    assert not df.duplicated(subset=["respondent_id"]).any(), "EN: Duplicate respondent_id in output\nFR: Doublons de respondent_id en sortie"
    return df


if __name__ == "__main__":
    df_clean = clean()
    df_clean.to_csv(CLEAN_PATH, index=False, encoding="utf-8")
    print(f"EN: Clean dataset saved to {CLEAN_PATH} — shape {df_clean.shape}")
    print(f"FR: Jeu de données propre enregistré dans {CLEAN_PATH} — forme {df_clean.shape}")
    print(df_clean.dtypes.to_string())
