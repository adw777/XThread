from bs4 import BeautifulSoup
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentProcessor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def process_url(self, url):
        """Process URL input and extract content"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Clean up the HTML
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find('h1') or soup.find('meta', property='og:title')
            if title_tag:
                title = title_tag.get_text() if title_tag.name == 'h1' else title_tag.get('content', '')
            
            # Extract content
            article = soup.find('article')
            if article:
                content = article.get_text(separator=' ', strip=True)
            else:
                content_div = soup.find(['div', 'main'], class_=lambda x: x and any(term in x.lower() for term in ['content', 'article', 'main', 'story']))
                content = content_div.get_text(separator=' ', strip=True) if content_div else soup.get_text(separator=' ', strip=True)
            
            # Extract image
            img_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img_url = og_image.get('content')
            
            return {
                'type': 'article',
                'title': title,
                'content': content[:4000],  # Limit content length
                'image_url': img_url,
                'source_url': url
            }
            
        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            raise

    def process_text(self, text):
        """Process direct text input"""
        return {
            'type': 'text',
            'content': text[:4000],  # Limit content length
            'title': text[:100] + "..." if len(text) > 100 else text
        }

    def process_thought(self, thought):
        """Process thought/topic input"""
        return {
            'type': 'thought',
            'content': thought,
            'title': thought[:100] + "..." if len(thought) > 100 else thought
        }

    def process_input(self, input_type, content):
        """Main processing method"""
        if input_type == 'url':
            return self.process_url(content)
        elif input_type == 'text':
            return self.process_text(content)
        elif input_type == 'thought':
            return self.process_thought(content)
        else:
            raise ValueError(f"Unknown input type: {input_type}")