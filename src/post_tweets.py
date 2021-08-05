import tweepy
from dotenv import load_dotenv
import os
import definitions
import datetime

"""
load_env
Loads environment variables (of API keys)
returns: dictionary of variables
"""
def load_env():
    env = {}
    load_dotenv()
    env["api_key"] = os.environ.get("API_KEY")
    env["api_secret_key"] = os.environ.get("API_SECRET_KEY")
    env["access_token"] = os.environ.get("ACCESS_TOKEN")
    env["access_token_secret"] = os.environ.get("ACCESS_TOKEN_SECRET")
    return env

"""
post
Creates Twitter thread with all defined regions
 vars: Environment variables (for secret API keys)
"""
def post():
    env = load_env()
    auth = tweepy.OAuthHandler(env["api_key"], env["api_secret_key"])
    auth.set_access_token(env["access_token"], env["access_token_secret"])
    api = tweepy.API(auth)

    # Posts tweets in all defined regions, with current images 
    regions_to_post = definitions.regions.keys()
    lastTweet = api.update_status(f"#COVID19 Daily Update - {datetime.date.today().strftime('%m/%d/%y')}\n\nSources:\nHHS: Hospitalizations and tests\nNYT: Cases and deaths") 
    for region in regions_to_post:
        media1 = api.media_upload(f"./images/graphs/{region}.png")
        media2 = api.media_upload(f"./images/tables/{region}.png")
        media3 = api.media_upload(f"./images/rt/{region}.png")
        if len(definitions.regions[region]) > 1 and region != "USA":
            regionString = region + " (" + ", ".join(definitions.regions[region]) + ")"
        else:
            regionString = region
        regionString += "\n*Beta-testing new hospitalization Rt plots. Interpret recent days with caution"
        lastTweet = api.update_status(f"{regionString}", in_reply_to_status_id=lastTweet.id, auto_populate_reply_metadata=True,media_ids=[media1.media_id, media2.media_id, media3.media_id])
        print(f"posted tweet: {regionString}")
