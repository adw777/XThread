from openai import OpenAI
import json
import logging
from .config import PERSONAS, THREAD_LENGTH_LIMITS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TweetGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate_tweets(self, processed_content, persona, persona_name=None):
        """Generate tweets based on persona and content"""
        if persona not in PERSONAS:
            raise ValueError(f"Unknown persona: {persona}")

        if persona == "copycat" and not persona_name:
            raise ValueError("Persona name required for copycat mode")

        # Get the appropriate prompt template
        if persona == "copycat":
            if persona_name not in PERSONAS[persona]["personas"]:
                raise ValueError(f"Unknown copycat persona: {persona_name}")
            
            persona_data = PERSONAS[persona]["personas"][persona_name]
            prompt = PERSONAS[persona]["prompt_template"].format(
                persona_name=persona_name,
                input_content=processed_content['content'],
                examples="\n".join(persona_data["examples"]),
                style_guide=persona_data["style_guide"]
            )
        else:
            prompt = PERSONAS[persona]["prompt_template"].format(
                input_content=processed_content['content']
            )

        # Generate content using OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a goat X user and poster, you are super active on X. Do not use hashtags."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Process the response
        content = response.choices[0].message.content.strip()
        tweets = [tweet.strip() for tweet in content.split('++') if tweet.strip()]

        # Limit number of tweets based on persona
        max_tweets = THREAD_LENGTH_LIMITS[persona]
        tweets = tweets[:max_tweets]

        # Format output
        output = {
            "tweets": []
        }

        for i, tweet_text in enumerate(tweets):
            tweet_obj = {
                "text": tweet_text[:250]  # Ensure tweet is within character limit
            }

            # Add image URL to first tweet if available
            if i == 0 and processed_content.get('type') == 'article' and processed_content.get('image_url'):
                tweet_obj["media"] = {
                    "urls": [processed_content['image_url']]
                }

            output["tweets"].append(tweet_obj)

        return output

    def save_tweets(self, tweets, filename='generated_tweets.json'):
        """Save generated tweets to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(tweets, file, indent=2, ensure_ascii=False)
                logger.info(f"Successfully saved {len(tweets['tweets'])} tweets to {filename}")
        except Exception as e:
            logger.error(f"Error saving JSON file: {str(e)}")
            raise