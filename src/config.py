"""
Program-level settings.

OUR_TEAM is the team this installation belongs to. Everything downstream
frames scouts as us-versus-them rather than as a neutral description of
the opponent, so this is the one value to change if another program
adopts the tool.
"""

OUR_TEAM = "Claremont-Mudd-Scripps"

# Defensive assignments to suggest per scout. Beyond about five the
# suggestions stop being actionable and start being a roster dump.
MAX_ASSIGNMENTS = 5

# An opponent needs at least this many minutes per game before we bother
# planning for them.
MIN_OPPONENT_MPG = 12

# One of ours needs at least this much floor time to be worth assigning.
MIN_DEFENDER_MPG = 10
