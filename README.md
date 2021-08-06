# covid-twitter-bot
Gets NYT/HHS COVID data, creates visualizations, and posts daily to Twitter [@jonahfleish](https://twitter.com/jonahfleish)
![image](https://pbs.twimg.com/media/E7wWvw-WEAUArNE?format=jpg&name=4096x4096)

# Dependencies
Python >= 3.8

Dependencies are listed in `requirements.txt`. Install with `pip install -r requirements.txt`

# How to run
1. Clone the directory

2.  To generate graphs and tables of all preset regions, run `python main.py [-tweet]`. 

- Optional argument `-tweet` or `-t` will post to Twitter, but requires environment variables with API keys.

# Visualizations
1. Two types of visualizations will be generated: tables in /images/tables and graphs in /images/graphs
2. By default the timeframe will range from March 2020 to today, but this can be changed in the function calls.
3. The regions to generate are specified in definitions.py. You can edit the regions dictionary to include any subsets of US states, PR, and DC
4. If you want to edit any visualizations, look at data-viz.py. Here, plot(), plot_table() create the main visualizations, and plot_four() and plot_tables() create the aggregate plots

# Contributing
- Feel free to leave Github issues if there is a new feature or bug you notice and I'll try to respond as soon as I can
- If you are interested in contributing, shoot me an email (jonah.fleishhacker@gmail.com)

![image](https://pbs.twimg.com/media/E7wWwDLWEAAZ8Vr?format=jpg&name=large)
![image](https://pbs.twimg.com/media/E7_oMr3WEAU7ux2?format=jpg&name=large)
