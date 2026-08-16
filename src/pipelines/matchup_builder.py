"""
Defensive matchup planning: who on our roster guards who on theirs.

The pairing decisions are made here in Python, not by the language model.
A 7B model asked to reason over raw stat lines will produce confident
nonsense; handed a finished pairing with its rationale, it writes it up
well. This is the same split the rest of the codebase already uses --
rules produce the facts, the model produces the prose.
"""

from src.config import (
    MAX_ASSIGNMENTS,
    MIN_DEFENDER_MPG,
    MIN_OPPONENT_MPG,
    OUR_TEAM,
)
from src.pipelines.scouting_context_builder import build_scouting_context


# --------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------

def _stats(player: dict) -> dict:
    return player.get("rule_based_profile", {}).get("stats", {}) or {}


def _labels(player: dict, key: str) -> list:
    return player.get("rule_based_profile", {}).get(key, []) or []


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def display_name(name: str) -> str:
    """Roster tables publish 'Ghai, Tanya'. Coaches say 'Tanya Ghai'."""
    name = str(name or "").strip()

    if "," in name:
        last, first = [part.strip() for part in name.split(",", 1)]
        if first and last:
            return f"{first} {last}"

    return name


def threat_score(player: dict) -> float:
    """How much of a problem this opponent is. Drives assignment order."""
    stats = _stats(player)
    return (
        _num(stats.get("ppg")) * 1.0
        + _num(stats.get("usage_rate")) * 25.0
        + _num(stats.get("mpg")) * 0.10
        + _num(stats.get("apg")) * 0.5
    )


def perimeter_defense_score(player: dict) -> float:
    """Fitness to guard a ball handler or shooter."""
    stats = _stats(player)
    score = _num(stats.get("spg")) * 3.0 + _num(stats.get("mpg")) * 0.06

    if "Defensive disruptor" in _labels(player, "defensive_profile"):
        score += 2.5
    if "Defensive specialist" in _labels(player, "defensive_profile"):
        score += 1.5

    # Bigs are poor choices to chase guards around screens.
    if _num(stats.get("rpg")) >= 7 and _num(stats.get("apg")) < 1.5:
        score -= 2.0

    return score


def interior_defense_score(player: dict) -> float:
    """Fitness to guard a post scorer or rebounder."""
    stats = _stats(player)
    score = (
        _num(stats.get("bpg")) * 3.5
        + _num(stats.get("rpg")) * 0.45
        + _num(stats.get("mpg")) * 0.04
    )

    if "Rim protector" in _labels(player, "defensive_profile"):
        score += 2.5

    return score


# --------------------------------------------------------------------
# Player shape
# --------------------------------------------------------------------

def is_interior_threat(player: dict) -> bool:
    stats = _stats(player)
    return (
        _num(stats.get("rpg")) >= 5.5
        or _num(stats.get("bpg")) >= 0.8
        or "Rebounding threat" in _labels(player, "rebounding_profile")
    )


def is_turnover_prone(player: dict) -> bool:
    """Handles the ball a lot and gives it away."""
    stats = _stats(player)
    ratio = _num(stats.get("assist_to_turnover"))
    return _num(stats.get("apg")) >= 2.0 and 0 < ratio < 1.1


def is_shooter(player: dict) -> bool:
    offensive = _labels(player, "offensive_profile")
    return "Three-point threat" in offensive or "3PT-heavy shot profile" in offensive


def describe_opponent(player: dict) -> str:
    stats = _stats(player)
    bits = [f"{_num(stats.get('ppg')):.1f} PPG"]

    usage = _num(stats.get("usage_rate"))
    if usage:
        bits.append(f"{usage * 100:.0f}% usage")

    ratio = _num(stats.get("assist_to_turnover"))
    if _num(stats.get("apg")) >= 2.0 and ratio:
        bits.append(f"{ratio:.1f} A/TO")

    if is_shooter(player):
        pct = _num(stats.get("three_pct"))
        bits.append(f"{pct * 100:.0f}% from three" if pct else "high 3PT volume")

    if is_interior_threat(player):
        bits.append(f"{_num(stats.get('rpg')):.1f} RPG")

    return ", ".join(bits)


def describe_defender(player: dict, interior: bool) -> str:
    stats = _stats(player)

    if interior:
        return f"{_num(stats.get('bpg')):.1f} BPG, {_num(stats.get('rpg')):.1f} RPG"

    return f"{_num(stats.get('spg')):.1f} SPG, {_num(stats.get('mpg')):.0f} MPG"


# --------------------------------------------------------------------
# Assignment
# --------------------------------------------------------------------

def _eligible(players: list, min_mpg: float) -> list:
    return [p for p in players if _num(_stats(p).get("mpg")) >= min_mpg]


def build_assignments(our_players: list, their_players: list) -> list:
    """
    Greedy: hardest opponent first, best available defender for that
    opponent's specific problem. Each defender is used once, so the coach
    gets a workable set of assignments rather than one player cloned.
    """
    threats = sorted(
        _eligible(their_players, MIN_OPPONENT_MPG),
        key=threat_score,
        reverse=True,
    )[:MAX_ASSIGNMENTS]

    available = list(_eligible(our_players, MIN_DEFENDER_MPG))
    assignments = []

    for threat in threats:
        if not available:
            break

        interior = is_interior_threat(threat)
        score = interior_defense_score if interior else perimeter_defense_score

        defender = max(available, key=score)
        available.remove(defender)

        assignments.append({
            "defender": display_name(defender["name"]),
            "defender_note": describe_defender(defender, interior),
            "assignment": display_name(threat["name"]),
            "assignment_note": describe_opponent(threat),
            "reason": _reason(defender, threat, interior),
            "emphasis": _emphasis(threat),
        })

    return assignments


def _reason(defender: dict, threat: dict, interior: bool) -> str:
    threat_stats = _stats(threat)
    defender_stats = _stats(defender)

    them = display_name(threat["name"])
    us = display_name(defender["name"])

    if interior:
        why_them = (
            f"{them} works inside -- {_num(threat_stats.get('rpg')):.1f} RPG "
            f"on {_num(threat_stats.get('ppg')):.1f} PPG"
        )
        why_us = (
            f"{us} is our best rim presence at "
            f"{_num(defender_stats.get('bpg')):.1f} BPG"
        )

    elif is_turnover_prone(threat):
        why_them = (
            f"{them} carries the offense at "
            f"{_num(threat_stats.get('usage_rate')) * 100:.0f}% usage but is loose "
            f"with it -- {_num(threat_stats.get('assist_to_turnover')):.1f} A/TO"
        )
        why_us = (
            f"{us} is our most disruptive defender at "
            f"{_num(defender_stats.get('spg')):.1f} SPG, so pressure should force turnovers"
        )

    elif is_shooter(threat):
        pct = _num(threat_stats.get("three_pct"))
        shooting = f"{pct * 100:.0f}% from three" if pct else "high three-point volume"
        why_them = f"{them} is a shooting threat at {shooting}"
        why_us = (
            f"{us} can stay attached and close out disciplined "
            f"({_num(defender_stats.get('spg')):.1f} SPG)"
        )

    else:
        ppg = _num(threat_stats.get("ppg"))
        role = "a primary scorer" if ppg >= 12 else (
            "a secondary scorer" if ppg >= 7 else "a rotation contributor"
        )
        why_them = f"{them} is {role} at {ppg:.1f} PPG"
        why_us = (
            f"{us} is our best available on-ball defender "
            f"({_num(defender_stats.get('spg')):.1f} SPG)"
        )

    return f"{why_them}. {why_us}."


def _emphasis(threat: dict) -> str:
    if is_turnover_prone(threat):
        return "Pressure the handler -- force the turnover"
    if is_shooter(threat):
        return "Deny the catch, no open threes"
    if is_interior_threat(threat):
        return "Front the post, help early on the roll"
    return "Make the catch difficult, contest everything"


# --------------------------------------------------------------------
# Team-level comparison
# --------------------------------------------------------------------

COMPARE_FIELDS = [
    ("ppg", "Points per game", True),
    ("opp_ppg", "Points allowed", False),
    ("fg_pct", "Field goal %", True),
    ("three_pct", "Three-point %", True),
    ("rebounds_per_game", "Rebounds per game", True),
    ("assists_per_game", "Assists per game", True),
]


def compare_teams(our_stats: dict, their_stats: dict) -> list:
    """Side-by-side on the handful of numbers a coach actually cites."""
    rows = []

    for key, label, higher_is_better in COMPARE_FIELDS:
        ours = our_stats.get(key)
        theirs = their_stats.get(key)

        if ours is None or theirs is None:
            continue

        ours, theirs = _num(ours), _num(theirs)
        if not ours and not theirs:
            continue

        if ours == theirs:
            edge = "Even"
        else:
            ours_better = (ours > theirs) if higher_is_better else (ours < theirs)
            edge = "Us" if ours_better else "Them"

        rows.append({
            "label": label,
            "ours": round(ours, 3),
            "theirs": round(theirs, 3),
            "edge": edge,
        })

    return rows


# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------

def build_matchup(
    opponent: str,
    our_team: str = OUR_TEAM,
    their_context: dict = None,
) -> dict:
    """
    Everything the packet needs to frame a scout as us-versus-them.

    Pass their_context when the caller has already built it -- assembling
    it involves classifier passes over the whole roster, and callers
    otherwise end up rebuilding the same thing several times per request.

    Degrades rather than raises: if our own team isn't cached yet, the
    opponent scout still works, just without assignments.
    """
    if their_context is None:
        their_context = build_scouting_context(opponent)

    try:
        our_context = build_scouting_context(our_team)
    except Exception as error:
        return {
            "our_team": our_team,
            "opponent": their_context.get("team_name", opponent),
            "available": False,
            "error": str(error),
            "assignments": [],
            "comparison": [],
            "our_players": [],
            "their_context": their_context,
        }

    our_players = our_context.get("players", [])
    their_players = their_context.get("players", [])

    return {
        "our_team": our_context.get("team_name", our_team),
        "opponent": their_context.get("team_name", opponent),
        "available": True,
        "assignments": build_assignments(our_players, their_players),
        "comparison": compare_teams(
            our_context.get("team_stats", {}) or {},
            their_context.get("team_stats", {}) or {},
        ),
        "our_players": our_players,
        "our_style": our_context.get("team_style", {}),
        "their_context": their_context,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_matchup("Chapman"), indent=2, default=str)[:4000])
