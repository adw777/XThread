from requests_oauthlib import OAuth1Session
import os
import json
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Path to your JSON file
TWEET_JSON_PATH = "shit2.json"  # Change this to your JSON file path

def load_tweet_from_json():
    """Load tweet content from a JSON file"""
    try:
        with open(TWEET_JSON_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        if not isinstance(data, dict) or 'tweets' not in data:
            raise ValueError("Invalid JSON format. Expected 'tweets' array in JSON")
            
        if not data['tweets'] or not isinstance(data['tweets'], list):
            raise ValueError("No tweets found in JSON or invalid format")
            
        # Get the first tweet's text
        tweet_content = data['tweets'][0].get('text')
        if not tweet_content:
            raise ValueError("No tweet text found in the first tweet")
            
        return {"text": tweet_content}
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading tweet from JSON: {str(e)}")
        raise

def get_oauth_session():
    """Initialize OAuth session and get request token"""
    consumer_key = os.environ.get("CONSUMER_KEY")
    consumer_secret = os.environ.get("CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        raise ValueError("Missing consumer key or consumer secret. Please check your .env file")

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
    """Authorize the token with user interaction"""
    consumer_key = os.environ.get("CONSUMER_KEY")
    consumer_secret = os.environ.get("CONSUMER_SECRET")
    
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print(f"\nPlease go here and authorize: {authorization_url}")
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
    """Post a tweet using the Twitter API"""
    consumer_key = os.environ.get("CONSUMER_KEY")
    consumer_secret = os.environ.get("CONSUMER_SECRET")
    
    try:
        # Get OAuth session
        oauth, resource_owner_key, resource_owner_secret = get_oauth_session()
        
        # Authorize token
        oauth_tokens = authorize_token(oauth, resource_owner_key, resource_owner_secret)
        
        # Create new OAuth session with access tokens
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=oauth_tokens["oauth_token"],
            resource_owner_secret=oauth_tokens["oauth_token_secret"],
        )

        # Post tweet
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
        # Load tweet from JSON
        logger.info(f"Loading tweet from {TWEET_JSON_PATH}")
        payload = load_tweet_from_json()
        
        # Preview the tweet
        logger.info(f"\nAbout to post the following tweet:\n{payload['text']}\n")
        confirmation = input("Do you want to post this tweet? (y/n): ")
        
        if confirmation.lower() != 'y':
            logger.info("Tweet posting cancelled")
            exit()
            
        # Post the tweet
        response = post_tweet(payload)
        print("\nTweet posted successfully!")
        print(json.dumps(response, indent=4, sort_keys=True))
        
    except Exception as e:
        logger.error(f"Failed to post tweet: {str(e)}")