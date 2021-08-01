import data_processing
import data_viz
import post_tweets
import sys

"""
run
 post = 
runs all scripts to fetch, clean, visualize, and post data
"""
def run(post = False):
    data_processing.get_data()
    data_viz.generate()
    if post:
        post_tweets.post_tweets()

# Parses command line arguments. Add a -t to post tweets
if __name__ == "__main__":
    a = False
    if len(sys.argv) > 1:
        a = sys.argv[1]
    if a in ['-t', '--t', '-tweet', '--tweet']:
        a = True
    else:
        a = False
    run(post = a)

