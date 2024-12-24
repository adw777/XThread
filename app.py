from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from genThread import TwitterThreadGenerator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Thread Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize thread generator
thread_generator = TwitterThreadGenerator(api_key=os.getenv('OPENAI_API_KEY'))

class URLInput(BaseModel):
    url: HttpUrl

class ThreadResponse(BaseModel):
    post: str
    platforms: List[str]
    twitterOptions: dict
    mediaUrls: Optional[List[str]] = None

@app.post("/generate-thread/", response_model=ThreadResponse)
async def create_thread(url_input: URLInput):
    try:
        article_content = thread_generator.extract_article_content(str(url_input.url))
        thread = thread_generator.generate_thread(article_content)
        return thread
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Thread Generator API is running. Use /generate-thread/ endpoint to create threads."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)