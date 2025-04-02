all: past_seasons current_season combine_games compute_elo

past_seasons:
	python nba_scores.py 2023-24 2022-23 2021-22

current_season:
	python nba_scores.py 2024-25

combine_games:
	python combine_seasons.py

compute_elo:
	python nba_elo.py



