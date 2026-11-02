"""Validation tests for the Kpankpanu cleaning pipeline.

EN: Tests validating every cleaning step of src/cleaning.py.
FR: Tests validant chaque étape de nettoyage de src/cleaning.py.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.cleaning import (
    CLEAN_PATH,
    RAW_PATH,
    RANDOM_SEED,
    clean,
    strip_columns,
)

SEED = RANDOM_SEED


@pytest.fixture(scope="module")
def raw() -> pd.DataFrame:
    return pd.read_excel(RAW_PATH)


@pytest.fixture(scope="module")
def clean_df() -> pd.DataFrame:
    return clean()


def test_raw_shape(raw: pd.DataFrame) -> None:
    """EN: Raw file must be 106 rows x 138 columns.
    FR: Le fichier brut doit faire 106 lignes x 138 colonnes."""
    assert raw.shape == (106, 138)


def test_clean_output_exists() -> None:
    """EN: The cleaned CSV must exist on disk.
    FR: Le CSV propre doit exister sur le disque."""
    assert CLEAN_PATH.is_file()


def test_clean_shape_and_columns(clean_df: pd.DataFrame) -> None:
    """EN: Clean dataset: 106 rows, all expected columns, no duplicate ids.
    FR: Jeu propre : 106 lignes, toutes les colonnes attendues, pas d'ids dupliqués."""
    assert clean_df.shape[0] == 106
    expected = [
        "respondent_id", "age", "income", "is_financially_dependent",
        "household_income", "education", "is_pregnant", "has_child_under_5",
        "num_children", "num_children_outlier", "num_children_missing",
        "ideal_price", "ideal_price_missing", "price_corrected",
        "low_price_respondent", "buy_intent",
        "perceived_child_benefit", "perceived_child_benefit_missing",
    ]
    assert list(clean_df.columns) == expected
    assert clean_df["respondent_id"].is_unique


def test_binary_targets(clean_df: pd.DataFrame) -> None:
    """EN: Dichotomous targets must be 0/1 with no missing values.
    FR: Les cibles dichotomiques doivent être 0/1 sans valeurs manquantes."""
    for col in ["is_pregnant", "has_child_under_5", "buy_intent"]:
        assert clean_df[col].isna().sum() == 0, f"{col} contains NaN"
        assert set(clean_df[col].dropna().unique()) <= {0, 1}, f"{col} not binary"


def test_ranges(clean_df: pd.DataFrame) -> None:
    """EN: age/income/ideal_price must stay in plausible ranges.
    FR: age/revenu/prix doivent rester dans des intervalles plausibles."""
    assert clean_df["age"].min() >= 15 and clean_df["age"].max() <= 60
    assert (clean_df["income"] >= 0).all()
    assert ((clean_df["ideal_price"] <= 5000) | clean_df["ideal_price"].isna()).all()


def test_price_typo_corrected(clean_df: pd.DataFrame) -> None:
    """EN: The 15001 typo must have been corrected; exactly one correction flagged.
    FR: La coquille 15001 doit avoir été corrigée ; exactement une correction signalée."""
    assert clean_df["price_corrected"].sum() == 1
    assert clean_df.loc[clean_df["price_corrected"] == 1, "ideal_price"].iloc[0] <= 2500


def test_skip_logic(clean_df: pd.DataFrame) -> None:
    """EN: Structural missingness must match the Kobo skip logic.
    FR: Les manquantes structurelles doivent respecter la logique de saut Kobo."""
    assert (
        clean_df["num_children"].isna() == (clean_df["has_child_under_5"] == 0)
    ).all()
    assert (
        clean_df["perceived_child_benefit"].isna() == (clean_df["has_child_under_5"] == 0)
    ).all()


def test_population(clean_df: pd.DataFrame) -> None:
    """EN: Every respondent is pregnant and/or mother of a child under 5.
    FR: Chaque répondante est enceinte et/ou mère d'un enfant de moins de 5 ans."""
    in_pop = (clean_df["is_pregnant"] == 1) | (clean_df["has_child_under_5"] == 1)
    assert in_pop.all()


def test_indicators(clean_df: pd.DataFrame) -> None:
    """EN: Derived indicators consistent with their source variables.
    FR: Les indicateurs dérivés cohérents avec leurs variables sources."""
    assert (clean_df["is_financially_dependent"] == (clean_df["income"] == 0)).all()
    assert (
        clean_df["low_price_respondent"]
        == ((clean_df["ideal_price"] <= 500) & clean_df["ideal_price"].notna())
    ).all()


def test_strip_columns(raw: pd.DataFrame) -> None:
    """EN: strip_columns removes trailing whitespace from column names.
    FR: strip_columns retire les espaces en fin de nom de colonne."""
    raw2 = pd.DataFrame(columns=["col  ", "autre  "])
    out = strip_columns(raw2)
    assert list(out.columns) == ["col", "autre"]


def test_seed_defined() -> None:
    """EN: RANDOM_SEED must be fixed for reproducibility.
    FR: RANDOM_SEED doit être fixé pour la reproductibilité."""
    assert SEED == 42


def test_clean_shape_and_columns(clean_df: pd.DataFrame) -> None:
    assert clean_df.shape[0] == 106
    expected = [
        "respondent_id", "age", "income", "is_financially_dependent",
        "household_income", "education", "is_pregnant", "has_child_under_5",
        "num_children", "num_children_outlier", "num_children_missing",
        "ideal_price", "ideal_price_missing", "ideal_price_imputed",  # NEW
        "price_corrected", "low_price_respondent", "buy_intent",
        "perceived_child_benefit", "perceived_child_benefit_missing",
    ]
    assert list(clean_df.columns) == expected
    assert clean_df["respondent_id"].is_unique


def test_price_imputation(clean_df: pd.DataFrame) -> None:
    """EN: All ideal_price must be filled, and imputed rows flagged.
    FR: Tous les ideal_price doivent être remplis, et les lignes imputées marquées."""
    assert clean_df["ideal_price"].isna().sum() == 0
    assert clean_df["ideal_price_imputed"].sum() == 9  # 9 non-responses in original data