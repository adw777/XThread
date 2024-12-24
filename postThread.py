import tweepy
import json
import time
import requests
from io import BytesIO
import webbrowser
import os
from dotenv import load_dotenv
from urllib.parse import parse_qs, urlparse

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
load_dotenv()

class TwitterPoster:
    def __init__(self, client_id, client_secret, redirect_uri="http://127.0.0.1"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.oauth2_user_handler = tweepy.OAuth2UserHandler(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=["tweet.read", "tweet.write", "users.read", "offline.access"]
        )

    def authenticate(self):
        try:
            # Get authorization URL and save the state
            authorization_url = self.oauth2_user_handler.get_authorization_url()
            self.saved_state = parse_qs(urlparse(authorization_url).query)['state'][0]
            
            print("\nPlease go to this URL to authorize the app:")
            print(authorization_url)
            
            webbrowser.open(authorization_url)
            
            print("\nAfter authorizing, you'll see a 'This site can't be reached' error - this is normal!")
            print("Copy the ENTIRE URL from your browser and paste it here:")
            full_response_url = input("Enter the full URL: ").strip()
            
            # Parse the response URL
            parsed_url = urlparse(full_response_url)
            params = parse_qs(parsed_url.query)
            
            # Verify state
            response_state = params['state'][0]
            if response_state != self.saved_state:
                raise ValueError("State mismatch! Possible CSRF attack.")
            
            # Get the code and fetch token
            code = params['code'][0]
            access_token = self.oauth2_user_handler.fetch_token(code)
            
            self.client = tweepy.Client(
                bearer_token=access_token["access_token"],
                consumer_key=self.client_id,
                consumer_secret=self.client_secret,
            )
            
            return access_token
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

    def post_thread(self, thread_json):
        if not hasattr(self, 'client'):
            print("Error: Not authenticated. Please authenticate first.")
            return

        tweets = thread_json['post'].split('\n\n')
        previous_tweet_id = None

        for i, tweet_text in enumerate(tweets, 1):
            try:
                response = self.client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_tweet_id if previous_tweet_id else None
                )
                
                previous_tweet_id = response.data['id']
                print(f"Tweet {i} posted successfully")
                time.sleep(1)
                
            except Exception as e:
                print(f"Error posting tweet {i}: {str(e)}")
                break

def main():
    try:
        with open('mechinterp.json', 'r', encoding='utf-8') as f:
            thread_json = json.load(f)
    except FileNotFoundError:
        print("Error: mechinterp.json not found")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in mechinterp.json")
        return

    poster = TwitterPoster(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET')
    )
    
    access_token = poster.authenticate()
    if access_token:
        print("\nAuthentication successful!")
        poster.post_thread(thread_json)
    else:
        print("Authentication failed. Please try again.")

if __name__ == "__main__":
    main()