from datetime import datetime


def get_current_season_label():
    now = datetime.now()

    if now.month >= 8:
        start_year = now.year
        end_year = now.year + 1
    else:
        start_year = now.year - 1
        end_year = now.year

    return f"{start_year}-{str(end_year)[-2:]}"