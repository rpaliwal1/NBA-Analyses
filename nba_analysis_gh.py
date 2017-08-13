import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Read Excel file
df = pd.read_excel('/Documents/NBA Analysis/Kobe_Bryant_PBP_All_Seasons.xlsx', sheetname='raw_data')

# Fill in NaN with 'N/A' (Location is 'NaN' when it's free throws)
df.fillna('N/A', inplace=True)

##### CLEANING UP DATA AND ADDING NEW COLUMNS #####

# Create Home vs Away column
df['Home or Away'] = df['Game'].apply(lambda title: 'Home' if 'at Los Angeles Lakers' in title else 'Away')

### Start parsing out 'Game' column
# Create date column by splitting 'Game' column
df['Date'] = df['Game'].apply(lambda game: game.split(',')[-2] + game.split(',')[-1])

# Convert 'Date' column to DateTime object
df['Date'] = pd.to_datetime(df['Date'], format=' %B %d %Y')

# Create 'Season' column from DateTime object
def get_season(col):
	if col.year == 2000:
		return 2001
	elif col.month < 5:
		return col.year
	else:
		return col.year + 1

df['Season'] = df['Date'].apply(get_season)
	
# Create 'Month' column from DateTime object, convert numbers to month names using dictionary
df['Month'] = df['Date'].apply(lambda d: d.month)
month_dict = {
	10: 'October',
	11: 'November',
	12: 'December',
	1: 'January',
	2: 'February',
	3: 'March',
	4: 'April'
				}

df['Month'] = df['Month'].apply(lambda m: month_dict.get(m))

# Create 'Opponent' column by splitting 'Game' column
def convert_game_to_opp(col):
	col = col.replace('Los Angeles Lakers', '').replace(' at ','').replace('Play-By-Play','')
	col = col.strip().split(',')
	return col[0]

df['Opponent'] = df['Game'].apply(convert_game_to_opp)

# Delete 'Game' column since all information has been parsed out from it
del df['Game']

# Clean up 'Shot Location' column
def clean_up_location(col):
	if col == 'N/A':
		return col
	elif ' of ' in col:
		return 'N/A'
	elif 'technical' in col:
		return 'N/A'
	else:
		col = col.split('(')[0]
		col = col.replace('at rim', '1').replace('from ', '').replace('ft', '')
		return int(col)

df['Shot Location'] = df['Shot Location'].apply(clean_up_location)

# Create 'Distance' column
def get_distance(col):
	if col == 'N/A':
		return col
	elif col == 1:
		return col
	elif col <= 5:
		return '2-5'
	elif col <= 10:
		return '6-10'
	elif col <= 15:
		return '11-15'
	elif col <= 20:
		return '16-20'
	elif col <= 25:
		return '21-25'
	elif col <= 30:
		return '26-30'
	else:
		return '31+'
	
df['Distance'] = df['Shot Location'].apply(get_distance)


### Start parsing out 'Play' column
# Get Make vs Miss
def get_make_or_miss(col):
	col = col.split()
	col = col[2]
	col = col.replace('misses','Miss').replace('makes','Make')
	return col

df['Make or Miss'] = df['Play'].apply(get_make_or_miss)

# Get 2 pointer vs 3 pointer vs free throw
def get_2_vs_3_vs_ft(col):
	if 'free throw' in col:
		return 1
	else:
		col = col.split()
		col = col[3]
		col = col.replace('-pt','')
		return int(col)

df['Points'] = df['Play'].apply(get_2_vs_3_vs_ft)

# Get player name
def get_player_name(col):
	col = col.split()
	col = col[0] + ' ' + col[1]
	return col

df['Player Name'] = df['Play'].apply(get_player_name)

# Delete 'Play' column since all information has been parsed out from it
del df['Play']

# Rearrange columns 
df_cols = df.columns.tolist()
df_cols = ['Season', 'Month', 'Date', 'Opponent', 'Home or Away', 'Time', 'Score', 'Player Name', 
		'Make or Miss', 'Points', 'Shot Location', 'Distance']
df = df[df_cols]

### DATA VISUALIZATIONS

# Box Plot by Month for 2005-2006 Season
g_box = df[(df['Season']==2006) & (df['Make or Miss']=='Make')].groupby(['Month','Date'])['Points'].sum()
g_box_df = g_box.to_frame().reset_index()
plt.figure(figsize=(10,6))
boxplot = sns.boxplot(x="Month", y="Points", order=['November','December','January','February','March','April'],
			data=g_box_df, palette='rainbow').set_title('Kobe Bryant - 2005-2006 Season Scoring by Month')
fig_box = boxplot.get_figure()
fig_box.savefig('/Documents/NBA Analysis/KB_05_06_boxplot.pdf')

# Heatmap by Attempted Shots
# Sort dataframe on 'Distance' for heatmap
df['Distance'] = pd.Categorical(df['Distance'],
							   categories=['2-5','6-10','11-15','16-20','21-25','26-30','31+'])
df.sort_values('Distance')

# Group By for Heatmap
g_hm1 = df[(df['Distance']!='N/A') & (df['Distance']!=1)].groupby(['Season','Distance'])['Points'].count()
g_hm2 = g_hm1.unstack(level=0)
		
# Create Heatmap		
plt.figure(figsize=(11,6))
ax = plt.axes()
heatmap = sns.heatmap(g_hm2)
ax.set_title('Kobe Bryant Heatmap - Shot Attempts by Location (excluding shots at the rim) \n', fontsize=13)
fig_hm = heatmap.get_figure()
fig_hm.savefig('/Documents/NBA Analysis/KB_heatmap.pdf')