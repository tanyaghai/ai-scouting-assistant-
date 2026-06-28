from datetime import datetime


def get_active_season_label(today=None):
    today = today or datetime.now()

    if today.month >= 8:
        start_year = today.year
        end_year = today.year + 1
    else:
        start_year = today.year - 1
        end_year = today.year

    return f"{start_year}-{str(end_year)[-2:]}"


def season_start_year(season: str) -> int:
    return int(season.split("-")[0])


def should_save_as_current(detected_season: str, today=None) -> bool:
    return detected_season == get_active_season_label(today)