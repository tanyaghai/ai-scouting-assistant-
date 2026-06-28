import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.models.team_feature_builder import build_team_feature_table


FEATURE_COLUMNS = [
    "ppg",
    "fg_pct",
    "three_pct",
    "rebounds_per_game",
    "assists_per_game",
    "turnovers_per_game",
    "blocks_per_game",
    "steals_per_game",
]


def scale_features(df: pd.DataFrame):
    features = df[FEATURE_COLUMNS].fillna(0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    return scaled, scaler


def evaluate_cluster_counts(df: pd.DataFrame, min_k: int = 2, max_k: int = 5):
    scaled, _ = scale_features(df)
    results = []

    for k in range(min_k, max_k + 1):
        if k >= len(df):
            continue

        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(scaled)

        results.append({
            "k": k,
            "inertia": round(model.inertia_, 2),
            "silhouette_score": round(silhouette_score(scaled, labels), 3),
        })

    return pd.DataFrame(results)


def summarize_team_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("team_archetype_cluster")[FEATURE_COLUMNS]
        .mean()
        .round(3)
        .reset_index()
    )


def name_team_archetype(row: pd.Series) -> str:
    ppg = row["ppg"]
    assists = row["assists_per_game"]
    rebounds = row["rebounds_per_game"]
    steals = row["steals_per_game"]
    turnovers = row["turnovers_per_game"]
    three_pct = row["three_pct"]

    if ppg >= 78 and assists >= 17:
        return "Elite offensive engine"

    if steals >= 11:
        return "Pressure defense team"

    if rebounds >= 40:
        return "Rebounding / physical team"

    if three_pct >= 0.33 and assists >= 14:
        return "Ball-movement shooting team"

    if turnovers >= 16:
        return "Turnover-prone team"

    return "Balanced team"


def explain_team_archetype(row: pd.Series) -> str:
    name = name_team_archetype(row)
    traits = []

    if row["ppg"] >= 70:
        traits.append("high scoring")
    if row["assists_per_game"] >= 14:
        traits.append("good ball movement")
    if row["rebounds_per_game"] >= 40:
        traits.append("strong rebounding")
    if row["steals_per_game"] >= 10:
        traits.append("defensive pressure")
    if row["turnovers_per_game"] >= 16:
        traits.append("turnover risk")
    if row["three_pct"] >= 0.33:
        traits.append("strong perimeter shooting")

    if traits:
        return f"{name}. Profile shows " + ", ".join(traits) + "."

    return f"{name}. No single extreme statistical identity."


def build_team_archetypes(n_clusters: int = 4) -> pd.DataFrame:
    df = build_team_feature_table()

    scaled, _ = scale_features(df)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    df["team_archetype_cluster"] = model.fit_predict(scaled)

    summaries = summarize_team_archetypes(df)
    summaries["team_ml_archetype"] = summaries.apply(name_team_archetype, axis=1)
    summaries["team_archetype_explanation"] = summaries.apply(explain_team_archetype, axis=1)

    name_map = dict(zip(summaries["team_archetype_cluster"], summaries["team_ml_archetype"]))
    explanation_map = dict(zip(summaries["team_archetype_cluster"], summaries["team_archetype_explanation"]))

    df["team_ml_archetype"] = df["team_archetype_cluster"].map(name_map)
    df["team_archetype_explanation"] = df["team_archetype_cluster"].map(explanation_map)

    return df

OUTPUT_PATH = "data/model_outputs/team_archetypes.csv"

if __name__ == "__main__":
    base_df = build_team_feature_table()

    print("\nCluster count evaluation:")
    print(evaluate_cluster_counts(base_df))

    clustered = build_team_archetypes(n_clusters=4)

    clustered.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved team archetypes to {OUTPUT_PATH}")

    print("\nTeam archetype summaries:")
    summaries = summarize_team_archetypes(clustered)
    summaries["team_ml_archetype"] = summaries.apply(name_team_archetype, axis=1)
    summaries["team_archetype_explanation"] = summaries.apply(explain_team_archetype, axis=1)
    print(summaries)

    print("\nTeams:")
    print(
        clustered[
            [
                "team",
                "season",
                "team_ml_archetype",
                "team_archetype_explanation",
                "team_archetype_cluster",
            ]
        ]
    )