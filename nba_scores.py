import pandas as pd
import requests
import sys

# Fix this to be dynamic
CURRENT_SEASON = "2024-25"

def main():
    if len(sys.argv) == 1:
        seasons = [CURRENT_SEASON]
    else:
        seasons = sys.argv[1:]
    print(f"Preparing to download game logs for seasons: {seasons}")
    for season in seasons:
        get_and_save_season(season)
    print("Done.")

def get_and_save_season(season):
    print(f"Reading data for {season} NBA season...")
    games = get_nba_games(season=season)
    out_file = f"data/nba-gamelog-{season}.csv"
    print(f"Writing data to {out_file}...")
    games.to_csv(out_file, index=False)

def get_nba_games(season="2024-25", date_from="", date_to=""):
    url = "https://stats.nba.com/stats/leaguegamelog"
    headers= {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        ),
        "Referer": "https://www.nba.com/",
    }
    params = {
        "Counter": "1000",
        "DateFrom": date_from,
        "DateTo": date_to,
        "Direction": "DESC",
        "LeagueID": "00",
        "PlayerOrTeam": "T",
        "Season": season,
        "SeasonType": "Regular Season",
        "Sorter": "DATE",
    }
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    rj = r.json()
    rows = rj["resultSets"][0]["rowSet"]
    columns = [col.lower() for col in rj["resultSets"][0]["headers"]]
    df = pd.DataFrame(rows, columns=columns)
    return df

if __name__ == "__main__":
    main()
    
