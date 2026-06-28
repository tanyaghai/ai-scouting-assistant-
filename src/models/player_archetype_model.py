from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.models.player_feature_builder import build_player_feature_table


FEATURE_COLUMNS = [
    "ppg",
    "rpg",
    "apg",
    "spg",
    "bpg",
    "mpg",
    "usage_rate",
    "ts_pct",
    "efg_pct",
    "three_point_rate",
    "free_throw_rate",
    "assist_to_turnover",
]

FEATURE_WEIGHTS = {
    "ppg": 1.2,
    "rpg": 1.25,
    "apg": 1.5,
    "spg": 1.2,
    "bpg": 1.25,
    "mpg": 0.9,
    "usage_rate": 1.4,
    "ts_pct": 1.0,
    "efg_pct": 1.0,
    "three_point_rate": 1.4,
    "free_throw_rate": 1.15,
    "assist_to_turnover": 1.25,
}

OUTPUT_DIR = Path("data/model_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_ml_players() -> pd.DataFrame:
    df = build_player_feature_table()
    return df[df["eligible_for_ml"]].reset_index(drop=True)


def scale_and_weight_features(df: pd.DataFrame):
    features = df[FEATURE_COLUMNS].fillna(0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    weighted = scaled.copy()

    for idx, col in enumerate(FEATURE_COLUMNS):
        weighted[:, idx] *= FEATURE_WEIGHTS.get(col, 1.0)

    return weighted, scaler


def evaluate_cluster_counts(df: pd.DataFrame, min_k: int = 3, max_k: int = 12) -> pd.DataFrame:
    features, _ = scale_and_weight_features(df)
    results = []

    for k in range(min_k, max_k + 1):
        if k >= len(df):
            continue

        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(features)

        results.append({
            "k": k,
            "inertia": round(model.inertia_, 2),
            "silhouette_score": round(silhouette_score(features, labels), 3),
        })

    return pd.DataFrame(results)


def summarize_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("archetype_cluster")[FEATURE_COLUMNS]
        .mean()
        .round(3)
        .reset_index()
    )


def build_league_averages(df: pd.DataFrame) -> dict:
    return df[FEATURE_COLUMNS].mean().to_dict()


def get_high_traits(cluster_row: pd.Series, league_avg: dict) -> list[str]:
    traits = []

    comparisons = {
        "ppg": "scoring",
        "rpg": "rebounding",
        "apg": "creation",
        "spg": "defensive activity",
        "bpg": "rim protection",
        "usage_rate": "usage",
        "three_point_rate": "3PT volume",
        "free_throw_rate": "free throw pressure",
        "assist_to_turnover": "ball security",
    }

    for stat, label in comparisons.items():
        value = cluster_row.get(stat, 0)
        avg = league_avg.get(stat, 0)

        if avg and value >= avg * 1.2:
            traits.append(label)

    return traits


def get_low_traits(cluster_row: pd.Series, league_avg: dict) -> list[str]:
    traits = []

    comparisons = {
        "ppg": "scoring",
        "rpg": "rebounding",
        "apg": "creation",
        "three_point_rate": "3PT volume",
        "free_throw_rate": "free throw pressure",
    }

    for stat, label in comparisons.items():
        value = cluster_row.get(stat, 0)
        avg = league_avg.get(stat, 0)

        if avg and value <= avg * 0.8:
            traits.append(label)

    return traits


def name_archetype(row: pd.Series) -> str:
    ppg = row["ppg"]
    rpg = row["rpg"]
    apg = row["apg"]
    spg = row["spg"]
    bpg = row["bpg"]
    usage = row["usage_rate"]
    three_rate = row["three_point_rate"]
    ft_rate = row["free_throw_rate"]

    if ppg >= 11 and rpg >= 6:
        return "Interior scorer / frontcourt engine"

    if apg >= 2.5 and ppg >= 8:
        return "Primary creator / lead guard"

    if three_rate >= 0.58:
        return "Spot-up shooter"

    if ppg >= 8 and three_rate >= 0.35:
        return "Perimeter scorer / wing"

    if ft_rate >= 0.4 and ppg >= 8:
        return "Slasher / contact scorer"

    if rpg >= 4.5 and ppg < 8:
        return "Glue forward / rebounder"

    if spg >= 1.2 and ppg < 8:
        return "Defensive rotation player"

    if usage >= 0.24 and ppg >= 8:
        return "High-usage scorer"

    return "Rotation contributor"


def explain_archetype(row: pd.Series, league_avg: dict) -> str:
    high_traits = get_high_traits(row, league_avg)
    low_traits = get_low_traits(row, league_avg)

    name = name_archetype(row)

    sentence = f"{name}. "

    if high_traits:
        sentence += "Above-average in " + ", ".join(high_traits) + ". "
    else:
        sentence += "Does not have one dominant above-average statistical trait. "

    if low_traits:
        sentence += "Lower relative profile in " + ", ".join(low_traits) + "."

    return sentence.strip()


def build_cluster_metadata(clustered_df: pd.DataFrame) -> pd.DataFrame:
    summaries = summarize_archetypes(clustered_df)
    league_avg = build_league_averages(clustered_df)

    summaries["ml_archetype"] = summaries.apply(name_archetype, axis=1)
    summaries["archetype_explanation"] = summaries.apply(
        lambda row: explain_archetype(row, league_avg),
        axis=1,
    )

    return summaries


def confidence_label(score):
    if score is None or pd.isna(score):
        return None

    if score >= 0.70:
        return "Strong archetype fit"
    elif score >= 0.45:
        return "Moderate archetype fit"
    elif score >= 0.25:
        return "Loose archetype fit"
    else:
        return "Weak / unusual archetype fit"


def add_confidence_scores(df: pd.DataFrame) -> pd.DataFrame:
    eligible = df[df["eligible_for_ml"]].copy()

    if eligible.empty:
        df["archetype_confidence"] = None
        df["archetype_fit_label"] = None
        return df

    max_distance = eligible["distance_to_centroid"].max()

    def confidence(distance):
        if distance is None or pd.isna(distance) or not max_distance:
            return None

        score = 1 - (distance / max_distance)
        return round(max(0, min(1, score)), 3)

    df["archetype_confidence"] = df["distance_to_centroid"].apply(confidence)
    df["archetype_fit_label"] = df["archetype_confidence"].apply(confidence_label)

    return df

def explain_player_archetype(row: pd.Series) -> str:
    if not row.get("eligible_for_ml"):
        return "Not enough minutes/games for reliable ML archetype."

    name = row.get("player")
    archetype = row.get("ml_archetype")
    fit = row.get("archetype_fit_label")

    return (
        f"{name} profiles as a {archetype} with a {fit.lower()}. "
        f"Stat profile: {row.get('ppg')} PPG, {row.get('rpg')} RPG, "
        f"{round(row.get('apg') or 0, 1)} APG, {round(row.get('spg') or 0, 1)} SPG, "
        f"{row.get('mpg')} MPG."
    )


def build_player_archetypes(n_clusters: int = 8) -> pd.DataFrame:
    eligible_df = get_ml_players()
    all_df = build_player_feature_table()

    features, _ = scale_and_weight_features(eligible_df)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)

    eligible_df = eligible_df.copy()
    eligible_df["archetype_cluster"] = model.fit_predict(features)

    metadata = build_cluster_metadata(eligible_df)

    name_map = dict(zip(metadata["archetype_cluster"], metadata["ml_archetype"]))
    explanation_map = dict(zip(metadata["archetype_cluster"], metadata["archetype_explanation"]))

    eligible_df["ml_archetype"] = eligible_df["archetype_cluster"].map(name_map)
    eligible_df["archetype_explanation"] = eligible_df["archetype_cluster"].map(explanation_map)

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(features)

    eligible_df["pca_x"] = coords[:, 0]
    eligible_df["pca_y"] = coords[:, 1]

    centroids = model.cluster_centers_
    distances = []

    for i, label in enumerate(eligible_df["archetype_cluster"]):
        player_vector = features[i]
        centroid = centroids[label]
        distance = ((player_vector - centroid) ** 2).sum() ** 0.5
        distances.append(round(distance, 3))

    eligible_df["distance_to_centroid"] = distances

    limited_df = all_df[~all_df["eligible_for_ml"]].copy()
    limited_df["archetype_cluster"] = None
    limited_df["ml_archetype"] = "Limited sample"
    limited_df["archetype_explanation"] = "Not enough minutes/games for reliable ML archetype."
    limited_df["pca_x"] = None
    limited_df["pca_y"] = None
    limited_df["distance_to_centroid"] = None

    final_df = pd.concat([eligible_df, limited_df], ignore_index=True)
    final_df = add_confidence_scores(final_df)
    
    final_df["player_archetype_explanation"] = final_df.apply(
    explain_player_archetype,
    axis=1,
)

    return final_df


def save_pca_plot(clustered: pd.DataFrame, filename: str = "player_archetype_pca.png") -> None:
    eligible = clustered[clustered["eligible_for_ml"]].copy()

    plt.figure(figsize=(10, 7))

    for archetype_name, group in eligible.groupby("ml_archetype"):
        plt.scatter(group["pca_x"], group["pca_y"], label=archetype_name, alpha=0.75)

    plt.title("Player Archetype Clusters")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.legend(fontsize=8)
    plt.tight_layout()

    path = OUTPUT_DIR / filename
    plt.savefig(path, dpi=200)
    plt.close()

    print(f"\nSaved PCA plot to {path}")


def save_outputs(clustered: pd.DataFrame) -> None:
    eligible_clustered = clustered[clustered["eligible_for_ml"]].copy()

    metadata = build_cluster_metadata(eligible_clustered)

    clustered.to_csv(OUTPUT_DIR / "player_archetypes.csv", index=False)
    metadata.to_csv(OUTPUT_DIR / "player_archetype_summaries.csv", index=False)


if __name__ == "__main__":
    base_df = get_ml_players()

    print("\nCluster count evaluation:")
    metrics = evaluate_cluster_counts(base_df)
    print(metrics)
    metrics.to_csv(OUTPUT_DIR / "player_cluster_metrics.csv", index=False)

    clustered = build_player_archetypes(n_clusters=8)
    save_outputs(clustered)

    print("\nCluster summaries:")
    summaries = build_cluster_metadata(clustered[clustered["eligible_for_ml"]].copy())
    print(summaries)

    print("\nPlayers by archetype:")
    for archetype_name in sorted(clustered["ml_archetype"].unique()):
        print(f"\n=== {archetype_name} ===")
        sample = clustered[clustered["ml_archetype"] == archetype_name]
        print(
            sample[
                [
                    "team",
                    "player",
                    "ppg",
                    "rpg",
                    "apg",
                    "mpg",
                    "usage_rate",
                    "three_point_rate",
                    "ml_archetype",
                    "archetype_cluster",
                    "archetype_fit_label",
                    "archetype_explanation",
                    "player_archetype_explanation",
                ]
            ]
        )

    save_pca_plot(clustered)