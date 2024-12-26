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
        self.client = OpenAI(api_key=api_key)
        
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
        
        prompt = f"""You're a subject matter expert who just read this article and want to share your insights. Write a thread that adds value by explaining the key points in your own words and providing additional context or analysis.

    The article is about: {article_content['title']}

    Article content: {cleaned_text[:4000]}

    Important guidelines:
    - Write in a natural, conversational tone like a real person would use
    - Avoid generic introductions or "thread" announcements
    - Don't use hashtags
    - Don't copy-paste from the article - explain concepts in your own words
    - Share genuine insights and analysis
    - Each tweet must be complete sentences and MUST be under 250 characters
    - Focus on what would actually interest or help your followers
    - Aim for 5-7 tweets max unless the topic truly needs more
    - End with something thought-provoking or actionable

    Format: Use '++' to separate tweets. Each tweet must be a complete thought under 250 characters."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an insightful AI expert who writes engaging, natural Twitter threads. Keep each tweet concise and complete, never exceeding 250 characters."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
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
            with open('sparseautoencoder.json', 'w', encoding='utf-8') as file:
                json.dump(output, file, indent=2, ensure_ascii=False)
                logger.info(f"Successfully saved thread with {len(tweets)} tweets to mechinterp.json")
        except Exception as e:
            logger.error(f"Error saving JSON file: {str(e)}")
            raise
        
        return output

def main():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
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