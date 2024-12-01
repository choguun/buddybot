import logging
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS, TEMPERATURE, TIMEOUT
import os

logger = logging.getLogger(__name__)

# Set the proxy environment variable if configured
if os.getenv('HTTPS_PROXY'):
    os.environ['HTTPS_PROXY'] = os.getenv('HTTPS_PROXY')

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_openai_response(text: str) -> str:
    """Get response from OpenAI for the user's question"""
    try:
        logger.info(f"Sending question to OpenAI: {text}")
        
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are Omi, a helpful AI assistant. Provide clear, concise, and friendly responses."},
                {"role": "user", "content": text}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=TIMEOUT
        )
        
        answer = response.choices[0].message.content.strip()
        logger.info(f"Received response from OpenAI: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Error getting OpenAI response: {str(e)}")
        return "I'm sorry, I encountered an error processing your request."