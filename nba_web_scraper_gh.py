import requests
import bs4
import re
import numpy as np
import pandas as pd

# Global variables
season_logs = []			# Stores each season's game log URL
pbp_all_games = []			# Stores each game's play by play box score URL
df = pd.DataFrame()			# Blank dataframe for when the script begins
games_played = {			# Dictionary where key = season, value = # of regular season games played to only scrape regular season games (exclude playoffs)
'01': 68,
'02': 80,
'03': 82,
'04': 65,
'05': 66,
'06': 80,
'07': 77,
'08': 82,
'09': 82,
'10': 73,
'11': 82,
'12': 58,
'13': 82,				# Starting with 2013 season, basketball-reference lists all 82 games (it will list inactive for games not played)
'14': 82,
'15': 82,
'16': 82
}

# Regex to parse out time, score, play, and location of shot. Home vs Away games appear differently in the source code.
regex_home = re.compile(r'''<td>(\d{1,2}:\d{2}\.\d)</td>				# Time
						\n(.*)<td\sclass=(.*)>
						(\d{1,3}-\d{1,3})</td>			# Score
						(.*)(K\.\sBryant)</a>			# Player name
						\s((misses|makes)			# Miss or make
						\s(\d-pt\sshot|				# 2 or 3 pt shot
						(technical\s|flagrant\s)?free\sthrow))	# Free throw
						(.*?)</td>				# Location
						''', re.VERBOSE)

regex_away = re.compile(r'''<td>(\d{1,2}:\d{2}\.\d)</td>				# Time
						\n(.*)<td\sclass=(.*)>
						(K\.\sBryant)</a>			# Player name
						\s((misses|makes)			# Miss or make
						\s(\d-pt\sshot|				# 2 or 3 pt shot
						(technical\s|flagrant\s)?free\sthrow))	# Free throw
						(.*?)					# Location
						</td><td\sclass=(.*)>
						(\d{1,3}-\d{1,3})			# Score
						''', re.VERBOSE)

# Using the player overview page, scrape each game log URL (1 per season)
def get_all_seasons(player_overview_url):
	player_overview = requests.get(player_overview_url)

	# Regex to scrape all game logs for each season
	season_logs_regex = re.compile(r'<a href=\"(/players/b/bryanko01/gamelog/(\d{4}))\">')

	# All game log URLs
	season_log_urls = season_logs_regex.findall(player_overview.text)

	# Loop through each game log URL
	for url in season_log_urls:
		# Skips game log URLs from before 2001 (play by play does not exist for these seasons)
		if int(url[1]) < 2001:
			continue
		# season_log_urls contains duplicates -- breaks out of loop when first duplicate URL is found
		elif 'https://www.basketball-reference.com{}'.format(url[0]) in season_logs:
			break
		# Otherwise, add game log URL to season_logs
		else:
			season_logs.append('https://www.basketball-reference.com{}'.format(url[0]))

	print('All {} seasons have been scraped from the player overview page.'.format(len(season_logs)))

# Using every season's game log URL, scrape each game URL
def get_all_games():

	# Loop through each game log URL
	for url in season_logs:
		season_log = requests.get(url)

		# Store the current and previous season in a variable for regex. This ensures that no other URLs are inadvertently scraped (i.e. 05-06 season only scrapes URLs with either 2005 or 2006 in them)
		season_num2 = url[-2:]
		season_num1 = str(int(season_num2) - 1)

		# Adds a '0' for 2000-2009 (i.e. '9' becomes '09')
		if len(season_num1) == 1:
			season_num1 = '0' + season_num1

		# Regex to scrape all games played during the season (regular season and playoffs)
		game_urls_regex = re.compile(r'<a href=\"(/boxscores/20({}|{})\w{}.html)\">'.format(season_num1, season_num2, '{8}'))

		# All game URL links
		game_urls = game_urls_regex.findall(season_log.text)

		# Loop through list of game URLs
		for index, url in enumerate(game_urls):
			# Breaks loop to scrape regular season games only based on games_played dictionary
			if index > (games_played.get(season_num2) - 1):
				break
			# Otherwise, add '/pbp/' to the link to get to the play by play breakdown and add URL to pbp_all_games
			else:
				url_pbp = url[0].replace('/boxscores/', '/boxscores/pbp/')
				pbp_all_games.append('https://www.basketball-reference.com{}'.format(url_pbp))

	print('All games have been scraped from each season log page.')

# Using every regular season game URL, scrape each of Kobe's scoring plays
def get_all_plays(regex, score_num, play_num_1, play_num_2, location_num):

	# Loop through each URL (each play by play box score)
	for url in pbp_all_games:
		res = requests.get(url)

		# Continue only if status code = 200
		while res.status_code != requests.codes.ok:
			print('Game URL did not return status code 200. Trying again...')
			res = requests.get(url)

		soup = bs4.BeautifulSoup(res.text, "lxml")

		# Blank dataframe to store full game. This later gets appended to final dataframe ('df')
		df_game = pd.DataFrame()

		# Grab H1, which will be the 'Game' column in the dataframe
		h1 = soup.select('h1')[0].getText()

		# Grab all data from the table that lists every play
		play_by_play = soup.select('.table_outer_container')

		# Find all matching text based on either home_regex or away_regex
		kobe_plays = regex.findall(res.text)

		# Continues loop if away regex is used on a home game, or vice versa
		if len(kobe_plays) == 0:
			continue

		# Loop through each play
		for play in kobe_plays:
			
			# Parse out each play into columns of a temporary dataframe. All of the variables (i.e. score_num, location_num, etc.) refer to groups in the RegEx.
			df_temp = pd.DataFrame({
									'Game': [h1],
									'Time': [play[0]],
									'Score': [play[score_num]],
									'Play': [play[play_num_1] + ' ' + play[play_num_2]],
									'Shot Location': [play[location_num]]
									})
			
			# Append each play to df_game since df_temp gets overwritten after every play
			df_game = df_game.append(df_temp, ignore_index=True)

		# After adding all plays to df_game, append df_game to df before moving on to next game
		global df
		df = df.append(df_game, ignore_index=True)
		print('{} has been added to the dataframe.'.format(h1))

# Run functions
get_all_seasons('https://www.basketball-reference.com/players/b/bryanko01.html')
get_all_games()
get_all_plays(regex_home, 3, 5, 6, -1)
get_all_plays(regex_away, -1, 3, 4, 8)

# Save to Excel
df.to_excel('Kobe_Bryant_PBP_All_Seasons.xlsx', sheet_name='raw_data')
print('Dataframe has been saved to Excel file!')
