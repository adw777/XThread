from requests_oauthlib import OAuth1Session
import os
import json
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# FOR POSTING A SINGLE TWEET!

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")

if not consumer_key or not consumer_secret:
    raise ValueError("Missing consumer key or consumer secret. Please check your .env file")

# content
payload = {
    "text": "pretraining coming to end... three things to look forward to- agents, synthetic data & inference time compute!"
}

def get_oauth_session():
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError as e:
        logger.error("Error with consumer_key or consumer_secret")
        raise e

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    logger.info(f"Got OAuth token: {resource_owner_key}")

    return oauth, resource_owner_key, resource_owner_secret

def authorize_token(oauth, resource_owner_key, resource_owner_secret):
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print(f"Please go here and authorize: {authorization_url}")
    verifier = input("Paste the PIN here: ")

    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    return oauth.fetch_access_token(access_token_url)

def post_tweet(payload):
    try:
        oauth, resource_owner_key, resource_owner_secret = get_oauth_session()
        
        oauth_tokens = authorize_token(oauth, resource_owner_key, resource_owner_secret)
        
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=oauth_tokens["oauth_token"],
            resource_owner_secret=oauth_tokens["oauth_token_secret"],
        )

        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )

        if response.status_code != 201:
            raise Exception(
                f"Request returned an error: {response.status_code} {response.text}"
            )

        logger.info(f"Response code: {response.status_code}")
        return response.json()

    except Exception as e:
        logger.error(f"Error posting tweet: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        response = post_tweet(payload)
        print(json.dumps(response, indent=4, sort_keys=True))
    except Exception as e:
        logger.error(f"Failed to post tweet: {str(e)}")