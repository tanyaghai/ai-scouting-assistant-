"""
scouting_metrics.py

Derives "second-layer" scouting stats from the box scores / season totals
your other collectors already cache (sidearm_collector, sciac_collector,
box_score_collector, recent_games_collector). Nothing here makes a network
request -- it only reads team_data dicts that are already in the cache
(via load_team_data) and computes new numbers from them.

Two levels of output:
  1. player_advanced_stats(player)      -> per-player efficiency stats
  2. team_advanced_stats(team_data)     -> team pace / four factors
  3. game_four_factors(a_players, b_players) -> single-game comparison,
     built from a box_score_collector.get_box_score_player_stats() result

All formulas are the standard basketball-analytics estimates (Dean Oliver /
Hollinger). They're approximations because we don't have play-by-play or
opponent shot charts -- that's noted inline wherever a formula has to skip
a term it can't see (e.g. game-level OREB isn't split out by
box_score_collector, so single-game possessions are a rougher estimate
than the season-level ones built from sidearm_collector roster totals).
"""

from src.storage.cache_manager import load_team_data
from src.data_collection.sidearm_collector import SCIAC_TEAM_STATS_URLS


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def to_float(value):
    """Coerce stat values (which may be None, '', numpy types, or strings
    like '12-34') into a float, or return None if that's not possible."""
    if value is None:
        return None
    try:
        if isinstance(value, str) and value.strip() in ("", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_div(numerator, denominator, default=None):
    num = to_float(numerator)
    den = to_float(denominator)
    if num is None or den is None or den == 0:
        return default
    return num / den


def round_or_none(value, digits=3):
    return None if value is None else round(value, digits)


# ---------------------------------------------------------------------------
# 1. player-level advanced stats (from sidearm_collector season totals)
# ---------------------------------------------------------------------------

def player_advanced_stats(player: dict, team_totals: dict = None) -> dict:
    """
    player: one dict from sidearm_collector.get_full_roster_stats()
            (season totals: fgm, fga, three_made, ftm, fta, points,
             off_rebounds, def_rebounds, assists, turnovers, steals,
             blocks, fouls, games, minutes, minutes_per_game)
    team_totals: optional dict from aggregate_team_totals_from_roster(),
            needed only for usage_rate
    """
    fgm = to_float(player.get("fgm"))
    fga = to_float(player.get("fga"))
    three_made = to_float(player.get("three_made"))
    three_att = to_float(player.get("three_attempts"))
    ftm = to_float(player.get("ftm"))
    fta = to_float(player.get("fta"))
    pts = to_float(player.get("points"))
    oreb = to_float(player.get("off_rebounds"))
    dreb = to_float(player.get("def_rebounds"))
    ast = to_float(player.get("assists"))
    tov = to_float(player.get("turnovers"))
    stl = to_float(player.get("steals"))
    blk = to_float(player.get("blocks"))
    pf = to_float(player.get("fouls"))
    games = to_float(player.get("games"))
    minutes = to_float(player.get("minutes"))

    # Effective FG%: gives 3s their proper extra weight vs raw FG%
    efg_pct = safe_div((fgm or 0) + 0.5 * (three_made or 0), fga)

    # True Shooting %: scoring efficiency counting FTs and 3s
    ts_pct = safe_div(pts, 2 * ((fga or 0) + 0.44 * (fta or 0))) if fga is not None else None

    # Shot selection
    three_point_rate = safe_div(three_att, fga)   # share of shots from three
    free_throw_rate = safe_div(fta, fga)          # how often they get to the line

    assist_to_turnover = safe_div(ast, tov)
    stocks_per_game = safe_div((stl or 0) + (blk or 0), games)

    # Hollinger-style Game Score, season total then per-game
    game_score_total = (
        (pts or 0)
        + 0.4 * (fgm or 0)
        - 0.7 * (fga or 0)
        - 0.4 * ((fta or 0) - (ftm or 0))
        + 0.7 * (oreb or 0)
        + 0.3 * (dreb or 0)
        + (stl or 0)
        + 0.7 * (ast or 0)
        + 0.7 * (blk or 0)
        - 0.4 * (pf or 0)
        - (tov or 0)
    )
    game_score_per_game = safe_div(game_score_total, games)

    # Per-40-minute rates, so bench players are comparable to starters
    per_40 = {}
    if minutes:
        for stat_name in ("points", "rebounds", "assists", "steals", "blocks", "turnovers"):
            total = to_float(player.get(stat_name))
            per_40[stat_name] = round_or_none(safe_div((total or 0) * 40, minutes), 1)

    result = {
        "name": player.get("name"),
        "efg_pct": round_or_none(efg_pct),
        "ts_pct": round_or_none(ts_pct),
        "three_point_rate": round_or_none(three_point_rate),
        "free_throw_rate": round_or_none(free_throw_rate),
        "assist_to_turnover": round_or_none(assist_to_turnover),
        "stocks_per_game": round_or_none(stocks_per_game, 1),
        "game_score_per_game": round_or_none(game_score_per_game, 1),
        "per_40": per_40,
    }

    if team_totals is not None:
        result["usage_rate"] = round_or_none(usage_rate(player, team_totals))

    return result


def usage_rate(player: dict, team_totals: dict) -> float:
    """
    Estimate of the share of a team's possessions a player "uses" while
    on the floor (Dean Oliver formula). Needs team totals for fga/fta/tov
    and total team minutes played (sum of all players' minutes).
    """
    fga = to_float(player.get("fga")) or 0
    fta = to_float(player.get("fta")) or 0
    tov = to_float(player.get("turnovers")) or 0
    minutes = to_float(player.get("minutes"))

    team_fga = team_totals.get("fga")
    team_fta = team_totals.get("fta")
    team_tov = team_totals.get("turnovers")
    team_minutes = team_totals.get("minutes")  # sum of all players' minutes

    if not minutes or not team_minutes or not team_fga:
        return None

    player_possessions_used = fga + 0.44 * fta + tov
    team_possessions_used = (team_fga or 0) + 0.44 * (team_fta or 0) + (team_tov or 0)

    numerator = player_possessions_used * (team_minutes / 5.0)
    denominator = minutes * team_possessions_used
    return safe_div(numerator, denominator)


# ---------------------------------------------------------------------------
# 2. team-level advanced stats (from sidearm roster totals + sciac team_stats)
# ---------------------------------------------------------------------------

ROSTER_SUM_FIELDS = [
    "fgm", "fga", "three_made", "three_attempts", "ftm", "fta",
    "off_rebounds", "def_rebounds", "rebounds", "fouls", "assists",
    "turnovers", "steals", "blocks", "points", "minutes",
]


def aggregate_team_totals_from_roster(players: list) -> dict:
    """Sum a roster's season totals into team-level totals. Used as the
    basis for pace/four-factors since sciac_collector's team_stats only
    has rates/per-game averages, not the raw FGA/FTA/TOV team needs for
    a possessions estimate."""
    totals = {field: 0.0 for field in ROSTER_SUM_FIELDS}
    max_games = 0

    for player in players:
        for field in ROSTER_SUM_FIELDS:
            value = to_float(player.get(field))
            if value is not None:
                totals[field] += value
        games = to_float(player.get("games"))
        if games is not None:
            max_games = max(max_games, games)

    totals["games"] = max_games or None
    return totals


def team_advanced_stats(team_data: dict) -> dict:
    """
    team_data: the dict shape produced by sciac_collector/sidearm_collector
               and returned by load_team_data(team_name), i.e.
               {"team_stats": {...}, "player_stats": [...]}
    """
    team_stats = team_data.get("team_stats", {}) or {}
    players = team_data.get("player_stats", []) or []
    totals = aggregate_team_totals_from_roster(players)
    games = totals.get("games") or to_float(team_stats.get("games"))

    # Possessions (Dean Oliver estimate): FGA - OREB + TOV + 0.44*FTA
    poss_total = None
    if totals["fga"] is not None:
        poss_total = (
            totals["fga"] - totals["off_rebounds"] + totals["turnovers"] + 0.44 * totals["fta"]
        )
    poss_per_game = safe_div(poss_total, games)

    ppg = to_float(team_stats.get("ppg")) or safe_div(totals["points"], games)
    opp_ppg = to_float(team_stats.get("opp_ppg"))

    off_rtg = safe_div(ppg, poss_per_game)
    off_rtg = off_rtg * 100 if off_rtg is not None else None

    def_rtg = safe_div(opp_ppg, poss_per_game)
    def_rtg = def_rtg * 100 if def_rtg is not None else None

    net_rtg = (off_rtg - def_rtg) if (off_rtg is not None and def_rtg is not None) else None

    efg_pct = safe_div(totals["fgm"] + 0.5 * totals["three_made"], totals["fga"])
    tov_pct = safe_div(totals["turnovers"], poss_total)
    tov_pct = tov_pct * 100 if tov_pct is not None else None
    ft_rate = safe_div(totals["fta"], totals["fga"])

    # Share of made FGs that were assisted -- a proxy for ball movement
    team_assist_rate = safe_div(totals["assists"], totals["fgm"])

    return {
        "games": games,
        "possessions_per_game": round_or_none(poss_per_game, 1),
        "off_rating_per_100": round_or_none(off_rtg, 1),
        "def_rating_per_100": round_or_none(def_rtg, 1),
        "net_rating_per_100": round_or_none(net_rtg, 1),
        "efg_pct": round_or_none(efg_pct),
        "tov_pct": round_or_none(tov_pct, 1),
        "ft_rate": round_or_none(ft_rate),
        "team_assist_rate": round_or_none(team_assist_rate),
        "_roster_totals": totals,  # handy if you want usage_rate() per player
    }


# ---------------------------------------------------------------------------
# 3. single-game four factors (from box_score_collector output)
# ---------------------------------------------------------------------------

GAME_SUM_FIELDS = [
    "fgm", "fga", "three_made", "three_attempts", "ftm", "fta",
    "rebounds", "fouls", "assists", "turnovers", "blocks", "steals", "points",
]


def _team_totals_from_box_score(players: list) -> dict:
    totals = {field: 0.0 for field in GAME_SUM_FIELDS}
    for player in players:
        for field in GAME_SUM_FIELDS:
            value = to_float(player.get(field))
            if value is not None:
                totals[field] += value
    return totals


def game_four_factors(team_a_players: list, team_b_players: list) -> dict:
    """
    team_a_players / team_b_players: the "team_one_players" /
    "team_two_players" lists from box_score_collector.get_box_score_player_stats()

    NOTE: box_score_collector doesn't split offensive vs. defensive
    rebounds, so the possessions estimate here drops the "-OREB" term
    that the season-level version above uses. That makes single-game
    possessions a bit high relative to the season number -- treat this
    as "shots + giveaways," good for comparing two teams' game flow,
    not for exact pace math.
    """
    a = _team_totals_from_box_score(team_a_players)
    b = _team_totals_from_box_score(team_b_players)

    def factors(team, opponent):
        efg_pct = safe_div(team["fgm"] + 0.5 * team["three_made"], team["fga"])
        poss_est = (team["fga"] or 0) + 0.44 * (team["fta"] or 0) + (team["turnovers"] or 0)
        tov_pct = safe_div(team["turnovers"], poss_est)
        tov_pct = tov_pct * 100 if tov_pct is not None else None
        ft_rate = safe_div(team["fta"], team["fga"])
        rebound_margin = (team["rebounds"] or 0) - (opponent["rebounds"] or 0)
        return {
            "points": team["points"],
            "efg_pct": round_or_none(efg_pct),
            "tov_pct": round_or_none(tov_pct, 1),
            "ft_rate": round_or_none(ft_rate),
            "rebound_margin": rebound_margin,
            "estimated_possessions": round_or_none(poss_est, 1),
        }

    return {
        "team_one": factors(a, b),
        "team_two": factors(b, a),
    }


# ---------------------------------------------------------------------------
# 4. roll-up for one team, ready to hand to the chatbot
# ---------------------------------------------------------------------------

def build_scouting_metrics(team_name: str) -> dict:
    team_data = load_team_data(team_name)
    players = team_data.get("player_stats", []) or []
    team_totals = aggregate_team_totals_from_roster(players)

    player_metrics = {
        player["name"]: player_advanced_stats(player, team_totals=team_totals)
        for player in players
        if player.get("name")
    }

    return {
        "team": team_name,
        "team_metrics": team_advanced_stats(team_data),
        "player_metrics": player_metrics,
    }


if __name__ == "__main__":
    for team_name in SCIAC_TEAM_STATS_URLS:
        try:
            metrics = build_scouting_metrics(team_name)
        except FileNotFoundError:
            print(f"No cached data yet for {team_name} -- run the collectors first.")
            continue

        print(f"\n=== {team_name} ===")
        print("Team:", metrics["team_metrics"])
        for name, stats in metrics["player_metrics"].items():
            print(f"  {name}: {stats}")
