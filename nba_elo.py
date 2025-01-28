from elo import Elo
import datetime
import pandas as pd
import numpy as np

GAME_CSV = "data/nba_games.csv"
OUT_FILE = "data/nba_latest_elo.csv"
K = 20
HOME_FIELD = 100

def main():
    print(f"Reading games from {GAME_CSV}...")
    nba_games = pd.read_csv(GAME_CSV)
    print(f"Retrieved {len(nba_games)} games.")
    nba_teams = set(
        list(nba_games["home_team"].unique()) +
        list(nba_games["away_team"].unique())
    )
    cur_season = current_season(nba_games)
    print(f"Season {cur_season} teams: {nba_teams}")
    nba_elo = Elo(teams=nba_teams, k=K, home_field=HOME_FIELD)
    games_with_elo = process_game_elo(nba_elo, nba_games)
    print(f"Writing games with updated Elo to {OUT_FILE}...")
    games_with_elo.to_csv("data/nba_latest_elo.csv", index=False)
    print("Writing Markdown table file...")
    write_markdown_output(games_with_elo, cur_season)
    abs_error = compute_error(games_with_elo, season=cur_season)
    print(f"Absolute error for 2024 with {K=}, {HOME_FIELD=}: {abs_error:.2f}")
    print("Done.")

def current_season(games):
    seasons = games["season"].unique()
    cur_season = max(seasons)
    return cur_season
    
def compute_error(df, season=None):
    df["abs_error"] = (df["actual_spread"] - df["point_spread"]).abs()
    if season:
        df = df[df["season"] == season]
    abs_error = df["abs_error"].sum()
    return abs_error
    
def process_game_elo(elo, games_input, verbose=False):
    # Copy for output
    games = games_input.copy()
    seasons = sorted(games["season"].unique())
    cur_season = seasons[-1]
    for season in seasons:
        print(f"{season} Season...")
        season_games = games[games["season"] == season]
        for ix, game in season_games.iterrows():
            if pd.isna(game["home_score"]):
                # Predict upcoming game, rather than update model
                home_team = game["home_team"]
                away_team = game["away_team"]
                away_elo = elo.team_rating(away_team)
                home_elo = elo.team_rating(home_team)
                home_win_prob = elo.home_win_prob(home_team, away_team)
                away_win_prob = 1 - home_win_prob
                point_spread = elo.point_spread(home_team, away_team)
                if verbose:
                    print(f"{game.season}, week {game.week}: "
                          f"{away_team} ({away_elo:.0f} - {away_win_prob:.0%}) "
                          f"{point_spread:.0f} at {home_team} ({home_elo:.0f} "
                          f"- {home_win_prob:.0%})")
                # Update model with game predictions
                games.at[ix, "home_elo"] = home_elo
                games.at[ix, "away_elo"] = away_elo
                games.at[ix, "home_win_prob"] = home_win_prob
                games.at[ix, "away_win_prob"] = away_win_prob
                games.at[ix, "point_spread"] = point_spread
            else:
                # Update model with games results
                home_team = game["home_team"]
                away_team = game["away_team"]
                away_elo = elo.team_rating(away_team)
                home_elo = elo.team_rating(home_team)
                home_win_prob = elo.home_win_prob(home_team, away_team)
                away_win_prob = 1 - home_win_prob
                point_spread = elo.point_spread(home_team, away_team)
                home_elo, away_elo, home_elo_post, away_elo_post = update_elo(elo, game)
                if verbose:
                    print(f"{game.season}, week {game.week}: "
                          f"{game.away_team} ({away_elo:.0f}-{away_elo_post:.0f}) "
                          f"{game.away_score:.0f} at {game.home_team} ({home_elo:.0f} "
                          f"- {home_elo_post:.0f}) {game.home_score:.0f}")
                # Update row with Elo values
                games.at[ix, "home_elo"] = home_elo
                games.at[ix, "away_elo"] = away_elo
                games.at[ix, "home_elo_post"] = home_elo_post
                games.at[ix, "away_elo_post"] = away_elo_post
                games.at[ix, "home_win_prob"] = home_win_prob
                games.at[ix, "away_win_prob"] = away_win_prob
                games.at[ix, "point_spread"] = point_spread
        print(f"End of season {season}")
        if season != cur_season:
            print("Regressing towards the mean between seasons...")
            elo.regress_towards_mean()
    return games
            
def update_elo(elo, game):
    home_team = game["home_team"]
    away_team = game["away_team"]
    pre_home = elo.team_rating(home_team)
    pre_away = elo.team_rating(away_team)
    elo.update_ratings(
        home_team,
        game["home_score"],
        away_team,
        game["away_score"],
    )
    post_home = elo.team_rating(home_team)
    post_away = elo.team_rating(away_team)
    return (
        pre_home,
        pre_away,
        post_home,
        post_away,
    )

def write_markdown_output(games, season):
    games_tbl = (games
                 .query(f"season == {season}")
                 .assign(actual_spread = lambda x: (x["away_score"] -
                                                    x["home_score"]))
                 .fillna(np.nan)
                 .replace([np.nan], None)
                 .filter(items=["week",
                                "away_team",
                                "away_elo",
                                "away_win_prob",
                                "away_score",
                                "home_team",
                                "home_elo",
                                "home_win_prob",
                                "home_score",
                                "point_spread",
                                "actual_spread"]))
    time_update_str = datetime.datetime.now().ctime()
    with open("nba_elo_table.md", "w") as out_file:
        out_file.write(f"## NBA Elo - {season} Season\n\n")
        out_file.write(f"*Updated {time_update_str}*\n\n")
        out_file.write(games_tbl.to_markdown(
            index=False,
            tablefmt="pipe",
            floatfmt=[".0f", "", ".0f", ".0%", ".0f", "", ".0f", ".0%", ".0f", ".0f", ".0f"],
            missingval="",
        ))


if __name__ == "__main__":
    main()
