# AGENTS.md — Règles pour l'Agent IA (Projet "Facteurs qui prédisent l'adoption d'une innovation alimentaire à visée nutritionnelle au Nord-Bénin : Approche analytique et Apprentissage automatique" )

## 🎯 Contexte du projet
Analyse de données d'enquête (106 répondantes, 138 variables) sur l'adoption d'une farine enrichie au Nord-Bénin. Objectif : nettoyage rigoureux, EDA, modélisation prédictive (Scikit-learn) et segmentation. **Ne jamais inventer de données ou de valeurs manquantes.**

## ⚙️ Commandes essentielles
- Lancer Jupyter : `uv run jupyter lab`
- Ajouter une dépendance : `uv add <package>`
- Exécuter les tests de validation : `uv run pytest -q` (si des tests existent)

## 🚦 Limites (Modèle à 3 niveaux)
- **Toujours (Always)** : Commenter chaque bloc de logique en anglais et en français. Valider chaque étape de nettoyage par une assertion (`assert df['col'].isna().sum() == 0`).
- **Demander avant (Ask first)** : Supprimer une colonne qui contient moins de 50 % de valeurs manquantes. Modifier la variable cible (`buy_intent`).
- **Ne jamais (Never)** : Modifier silencieusement les labels, les splits d'entraînement, ou les règles de prétraitement. Ne pas toucher aux fichiers dans `data/raw/`.

## 📂 Structure et style
- **Notebooks** (`notebooks/`) : Pour le traitement de la base , l'exploration et la visualisation. La logique réutilisable va dans `src/`.
    **01_data_cleaning.ipynb** : Nettoyage pur
    **02_exploratory_analysis.ipynb** : Analyse exploratoire et visualisation.
    **03_machine_learning.ipynb** : Modélisation et apprentissage automatique.

- **Code Python** : Style PEP 8, noms de variables en anglais, commentaires bilingues (EN puis FR).
- **Données** : Les données brutes sont en lecture seule. Les données nettoyées vont dans `data/processed/`.

## 🧪 Règles Data Science
- **Avant toute modélisation** : Inspecter le schéma, les types, les valeurs manquantes, les doublons et les risques de fuite de données (`data leakage`).
- **Définir la métrique et la baseline** avant l'entraînement. Ne jamais affirmer qu'un modèle est meilleur sans le comparer à une baseline.
- **Reproductibilité** : Fixer une `random_seed` et documenter les splits (train/validation/test).
- **Rapports** : Sauvegarder les figures et les métriques dans `reports/`. Résumer les résultats dans le README à la fin de chaque session.