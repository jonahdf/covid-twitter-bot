import tweepy
from dotenv import load_dotenv
import os
import definitions
import datetime
import random, string
import time

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

load_dotenv()
api_key = os.environ.get("API_KEY")
api_secret_key = os.environ.get("API_SECRET_KEY")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
auth = tweepy.OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

regions_to_post = definitions.regions.keys()
lastTweet = api.update_status(f"COVID Daily Update - {datetime.date.today().strftime('%m/%d/%y')}\n\nSources:\nHHS - Hospitalizations and tests\nNYT - Cases and deaths") 
for region in regions_to_post:
    media1 = api.media_upload(f"./images/graphs/{region}.png")
    media2 = api.media_upload(f"./images/tables/{region}.png")
    if len(definitions.regions[region]) > 1 and region != "USA":
        regionString = region + " (" + ", ".join(definitions.regions[region]) + ")"
    else:
        regionString = region

    lastTweet = api.update_status(f"{regionString}", in_reply_to_status_id=lastTweet.id, auto_populate_reply_metadata=True,media_ids=[media1.media_id, media2.media_id])
    print(f"posted tweet: {regionString}")