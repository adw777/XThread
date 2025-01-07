import requests
import json
import os
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TwitterThreadGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
        
    def extract_article_content(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        title = ""
        title_tag = soup.find('h1') or soup.find('meta', property='og:title')
        if title_tag:
            title = title_tag.get_text() if title_tag.name == 'h1' else title_tag.get('content', '')
        
        article = soup.find('article')
        if article:
            content = article.get_text(separator=' ', strip=True)
        else:
            content_div = soup.find(['div', 'main'], class_=lambda x: x and any(term in x.lower() for term in ['content', 'article', 'main', 'story']))
            content = content_div.get_text(separator=' ', strip=True) if content_div else soup.get_text(separator=' ', strip=True)
        
        img_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_url = og_image.get('content')
        
        return {
            'title': title,
            'text': content,
            'top_image': img_url
        }

    def generate_thread(self, article_content, include_image=True):
        cleaned_text = ' '.join(article_content['text'].split())
        logger.info(f"Article title: {article_content['title']}")
        logger.info(f"Content length: {len(cleaned_text)}")
        
        # Create a more focused prompt
        prompt = f"""Write an engaging Twitter thread explaining this topic in detail from 
        first principles. Break down the key concepts in simple terms and explain with examples.

        Title: {article_content['title']}

        Key content to analyze: {cleaned_text[:8000]}  # Reduced content length

        Requirements:
        1. Write tweets that explain the main ideas with super high agency
        2. Make complex concepts accessible, use super good examples for exmplanation
        3. Be factual and to the point like elon musk
        4. No hashtags no bullshit
        5. Each tweet must be under 250 characters, cause we dont have premium, but you can add as many tweets you want, its a thread after all

        Separate each tweet with '++'"""
        
        logger.info("Sending request to Grok API...")

        try:
            response = self.client.chat.completions.create(
                model="grok-2-latest",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are just like Elon Musk, write super cool, to the point & worthy enough Twitter threads that people wait for everyday."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,  # Increased max tokens
                temperature=0.7
            )
            
            logger.info(f"Raw response from API: {response}")
            
            if not response.choices[0].message.content:
                logger.error("Received empty response from API")
                raise ValueError("Empty response from API")
                
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise
        
        thread_content = response.choices[0].message.content.strip()
        tweets = [tweet.strip() for tweet in thread_content.split('++') if tweet.strip()]
        
        output = {
            "tweets": []
        }
        
        for i, tweet_text in enumerate(tweets):
            cleaned_tweet = tweet_text.strip()
            
            if len(cleaned_tweet) > 250:
                sentences = cleaned_tweet.split('. ')
                truncated_tweet = ''
                for sentence in sentences:
                    if len(truncated_tweet + sentence + '.') <= 250:
                        truncated_tweet += sentence + '. '
                    else:
                        break
                cleaned_tweet = truncated_tweet.strip()
            
            tweet_obj = {
                "text": cleaned_tweet
            }
            
            if i == 0 and include_image and article_content['top_image']:
                tweet_obj["media"] = {
                    "urls": [article_content['top_image']]
                }
            
            output["tweets"].append(tweet_obj)
        
        try:
            with open('grok2.json', 'w', encoding='utf-8') as file:
                json.dump(output, file, indent=2, ensure_ascii=False)
                logger.info(f"Successfully saved thread with {len(tweets)} tweets to new.json")
        except Exception as e:
            logger.error(f"Error saving JSON file: {str(e)}")
            raise
        
        return output

def main():
    api_key = os.getenv('XAI_API_KEY')

    if not api_key:
        raise ValueError("Please set XAI_API_KEY environment variable")
    
    generator = TwitterThreadGenerator(api_key)
    url = input("Enter the article URL: ")
    
    try:
        article_content = generator.extract_article_content(url)
        thread = generator.generate_thread(article_content)
        print("\nGenerated Thread JSON:")
        print(json.dumps(thread, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()