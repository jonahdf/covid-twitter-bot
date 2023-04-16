import data_processing
import data_viz
import post_tweets
import sys

"""
run
 post = 
runs all scripts to fetch, clean, visualize, and post data
"""
def run(post = False, dev = False):
    newestData = data_processing.DataSets(from_csv = dev)
    data_viz.generate(newestData)
    if post:
        post_tweets.post()

# Parses command line arguments. Add a -t to post tweets 
if __name__ == "__main__":
    shouldTweet = False
    shouldDev = False
    if len(sys.argv) > 1:
        a = sys.argv[1]
    if a in ['-t', '--t', '-tweet', '--tweet']:
        shouldTweet = True
    else:
        shouldTweet = False
    if a in ['-d', '--d', '-dev', '--dev']:
        shouldDev = True
    else:
        shouldDev = False
    
    run(post = shouldTweet, dev = shouldDev)

