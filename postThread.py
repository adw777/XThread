from requests_oauthlib import OAuth1Session
import requests
import os
import json
from dotenv import load_dotenv
import logging
import time
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")

if not consumer_key or not consumer_secret:
    raise ValueError("Missing consumer key or consumer secret. Please check your .env file")

def load_tweet_content():
    """Load tweet content from mechinterp.json file"""
    try:
        with open('sparseautoencoder.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            if 'tweets' not in data:
                raise ValueError("JSON file must contain a 'tweets' array")
            return data['tweets']
    except FileNotFoundError:
        logger.error("mechinterp.json file not found in the current directory")
        raise
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in mechinterp.json")
        raise
    except Exception as e:
        logger.error(f"Error reading tweet content: {str(e)}")
        raise

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

def post_tweet_thread(tweets):
    try:
        oauth, resource_owner_key, resource_owner_secret = get_oauth_session()
        
        oauth_tokens = authorize_token(oauth, resource_owner_key, resource_owner_secret)
        
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=oauth_tokens["oauth_token"],
            resource_owner_secret=oauth_tokens["oauth_token_secret"],
        )

        previous_tweet_id = None
        responses = []
        
        logger.info("Waiting 30 seconds before starting to post...")
        time.sleep(30)
        
        for i, tweet in enumerate(tweets):
            max_retries = 5  
            retry_delay = 120  
            
            for attempt in range(max_retries):
                try:
                    tweet_text = tweet["text"]
                    if i > 0:
                        tweet_text = f"{tweet_text} ·{i}"
                    
                    payload = {
                        "text": tweet_text
                    }
                    
                    if previous_tweet_id:
                        payload["reply"] = {"in_reply_to_tweet_id": previous_tweet_id}
                    
                    if "media" in tweet and "urls" in tweet["media"]:
                        media_ids = [upload_media(oauth, url) for url in tweet["media"]["urls"]]
                        if media_ids:
                            payload["media"] = {"media_ids": media_ids}
                    
                    logger.info(f"Attempting to post tweet {i+1} of {len(tweets)}")
                    response = oauth.post(
                        "https://api.twitter.com/2/tweets",
                        json=payload,
                    )

                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            logger.warning(f"Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 1}")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Max retries reached for rate limit")

                    if response.status_code != 201:
                        raise Exception(
                            f"Request returned an error: {response.status_code} {response.text}"
                        )

                    response_json = response.json()
                    responses.append(response_json)
                    previous_tweet_id = response_json["data"]["id"]
                    
                    logger.info(f"Successfully posted tweet {i+1}")
                    
                    wait_time = 30 + (i * 5)  
                    logger.info(f"Waiting {wait_time} seconds before next tweet...")
                    time.sleep(wait_time)
                    
                    break
                    
                except RequestException as e:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Request failed. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise

        logger.info(f"Successfully posted thread of {len(tweets)} tweets")
        return responses

    except Exception as e:
        logger.error(f"Error posting tweet thread: {str(e)}")
        raise

def upload_media(oauth, media_url):
    """
    Upload media to Twitter and return media_id
    Note: This is a placeholder function - you'll need to implement the actual
    media upload logic using Twitter's media upload endpoint
    """
    try:
        media_response = requests.get(media_url)
        media_response.raise_for_status()
        
        upload_response = oauth.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            files={"media": media_response.content}
        )
        
        if upload_response.status_code != 200:
            raise Exception(f"Media upload failed: {upload_response.text}")
        
        return upload_response.json()["media_id_string"]
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        tweets = load_tweet_content()
        logger.info(f"Loaded thread with {len(tweets)} tweets")
        
        responses = post_tweet_thread(tweets)
        print(json.dumps(responses, indent=4, sort_keys=True))
    except Exception as e:
        logger.error(f"Failed to post thread: {str(e)}")