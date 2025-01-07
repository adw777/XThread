import os
from dotenv import load_dotenv
import argparse
from xitdamn.inputTaken import ContentProcessor
from xitdamn.generator import TweetGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate X posts with different personas')
    parser.add_argument('--input-type', choices=['url', 'text', 'thought'], required=True,
                      help='Type of input content')
    parser.add_argument('--content', required=True,
                      help='The actual content (URL, text, or thought)')
    parser.add_argument('--persona', choices=['shitposter', 'elaborative', 'copycat'], required=True,
                      help='Persona to use for generation')
    parser.add_argument('--persona-name', choices=['elon', 'sam', 'AD'],
                      help='Required for copycat persona')
    parser.add_argument('--output', default='generated_tweets.json',
                      help='Output JSON file name')

    args = parser.parse_args()

    # Validate arguments
    if args.persona == 'copycat' and not args.persona_name:
        parser.error("--persona-name is required when using copycat persona")

    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")

    try:
        # Process input content
        processor = ContentProcessor()
        processed_content = processor.process_input(args.input_type, args.content)
        
        # Generate tweets
        generator = TweetGenerator(api_key)
        tweets = generator.generate_tweets(
            processed_content,
            args.persona,
            args.persona_name
        )
        
        # Save output
        generator.save_tweets(tweets, args.output)
        
        logger.info(f"Successfully generated tweets and saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()



# run commands
"""
# for url w/ elaborative persona
python main.py --input-type url --content "https://example.com/article" --persona elaborative --output tweets.json

# for thought w/ copycat elon
python main.py --input-type thought --content "AI is evolving faster than expected" --persona copycat --persona-name elon --output tweets.json

# for text w/ shitposter
python main.py --input-type text --content "Your text content here" --persona shitposter --output tweets.json

"""