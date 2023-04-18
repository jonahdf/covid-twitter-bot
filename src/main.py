import data_processing
import data_viz
import post_tweets
import sys
from datetime import datetime, timezone, timedelta

"""
run
 post = 
runs all scripts to fetch, clean, visualize, and post data
"""


def run(post=False, dev=False):
    # Workaround for Heroku Scheduler: Only run if it's a Sunday
    # Get current time in Pacific Time
    pac_time = datetime.now(timezone(timedelta(hours=-7)))
    if pac_time.weekday() != 6 and not dev:
        print("Not a Sunday. Won't post")
        exit()
    newestData = data_processing.DataSets(from_csv=dev)
    data_viz.generate(newestData)
    if post:
        post_tweets.post()


# Parses command line arguments. Add a -t to post tweets
if __name__ == "__main__":
    shouldTweet = False
    shouldDev = False
    a = False
    if len(sys.argv) > 1:
        a = sys.argv[1]
    if a in ["-t", "--t", "-tweet", "--tweet"]:
        shouldTweet = True
    else:
        shouldTweet = False
    if a in ["-d", "--d", "-dev", "--dev"]:
        shouldDev = True
    else:
        shouldDev = False

    run(post=shouldTweet, dev=shouldDev)

run()
