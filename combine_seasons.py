import glob
import pandas as pd

# season_id                  22023
# team_id               1610612746
# team_abbreviation            LAC
# team_name            LA Clippers
# game_id                 22300379
# game_date             2023-12-21
# matchup                LAC @ OKC
# wl                             L
# min                          240
# fgm                           44
# fga                           93
# fg_pct                     0.473
# fg3m                          17
# fg3a                          43
# fg3_pct                    0.395
# ftm                           10
# fta                           12
# ft_pct                     0.833
# oreb                          12
# dreb                          28
# reb                           40
# ast                           23
# stl                            9
# blk                            5
# tov                           16
# pf                            18
# pts                          115
# plus_minus                   -19
# video_available                1

columns = [
    "season",
    "game_id",
    "game_date",
    "team_id",
    "team_abbreviation",
    "team_name",
    "pts",
]

home_rename = {
    "team_id": "home_team_id",
    "team_abbreviation": "home_team_abbr",
    "team_name": "home_team",
    "pts": "home_score",
}

away_rename = {
    "team_id": "away_team_id",
    "team_abbreviation": "away_team_abbr",
    "team_name": "away_team",
    "pts": "away_score",
}

def main():
    season_files = glob.glob("data/nba-gamelog-*.csv")
    print(f"Combining season files: {season_files}")
    df_list = [pd.read_csv(fn) for fn in season_files]
    df = (pd.concat(df_list, ignore_index=True)
          .assign(season = lambda x: x["season_id"] - 20000))
    df_away = (df[df["matchup"].str.contains("@")]
               [columns]
               .rename(columns=away_rename))
    print(f"Found {len(df_away)} away games")
    df_home = (df[~df["matchup"].str.contains("@")]
               [columns]
               .rename(columns=home_rename))
    print(f"Found {len(df_home)} home games")
    games = (pd.merge(
        df_away,
        df_home,
        how="inner",
        on=["season", "game_id", "game_date"],
    ).assign(
        actual_spread = lambda x: (x["away_score"] - x["home_score"])
    ).sort_values("game_date"))
    print(f"Combined into {len(games)} actual matchups")
    out_file = "data/nba_games.csv"
    print(f"Writing output file {out_file}...")
    games.to_csv(out_file, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
