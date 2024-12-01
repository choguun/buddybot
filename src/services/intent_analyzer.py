import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import (
    OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS, TEMPERATURE, TIMEOUT,
    OPENWEATHER_API_KEY
)
from src.services.weather_service import WeatherService
from src.services.calendar_service import CalendarService
import os
import json
import datetime

logger = logging.getLogger(__name__)

# Initialize OpenAI client with proper configuration
client_kwargs = {
    'api_key': OPENAI_API_KEY,
}

# Only add proxy if it's configured
if os.getenv('HTTPS_PROXY'):
    # For newer versions of openai, we need to handle proxies differently
    os.environ['OPENAI_PROXY'] = os.getenv('HTTPS_PROXY')

client = OpenAI(**client_kwargs)

# Initialize Weather service
weather_service = WeatherService(OPENWEATHER_API_KEY)

# Define supported intents
SUPPORTED_INTENTS = {
    'weather': ['weather', 'temperature', 'forecast', 'rain', 'sunny'],
    'calendar': ['schedule', 'appointment', 'meeting', 'calendar', 'event'],
    'email': ['email', 'mail', 'inbox', 'message', 'send'],
    'drinking': ['drink', 'alcohol', 'beer', 'wine', 'drunk']
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def analyze_intent(text: str) -> dict:
    """
    Analyze text to detect user intents using OpenAI
    Returns a dictionary with detected intents and confidence scores
    """
    try:
        logger.info(f"Analyzing intent for text: {text}")
        
        system_prompt = """You are an AI that analyzes user messages to detect their intent.
        Respond with a JSON object containing these fields:
        - primary_intent: The main intent detected (weather, calendar, email, drinking, or unknown)
        - confidence: A score from 0 to 1 indicating confidence in the detection
        - entities: Any relevant entities mentioned (dates, locations, people, etc.)
        - requires_clarification: Boolean indicating if user input needs clarification
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message: {text}"}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=TIMEOUT,
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Intent analysis result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error analyzing intent: {str(e)}")
        return {
            "primary_intent": "unknown",
            "confidence": 0,
            "entities": [],
            "requires_clarification": True
        }

def get_intent_response(intent_data: dict) -> str:
    """Generate appropriate response based on detected intent"""
    
    intent = intent_data.get('primary_intent', 'unknown')
    confidence = intent_data.get('confidence', 0)
    entities = intent_data.get('entities', [])
    needs_clarification = intent_data.get('requires_clarification', True)
    
    if needs_clarification:
        return "I'm not sure what you're asking. Could you please be more specific?"
    
    if confidence < 0.7:
        return "I'm not quite sure what you want to do. Could you rephrase that?"
    
    # Handle weather intent with actual weather data
    if intent == 'weather':
        location = next((entity for entity in entities if entity.get('type') == 'location'), None)
        if not location:
            return "Which city would you like to know the weather for?"
            
        weather_data = weather_service.get_weather(location.get('value', ''))
        if weather_data:
            return (
                f"Current weather in {weather_data['location']}, {weather_data['country']}:\n"
                f"Temperature: {weather_data['temperature']}°C\n"
                f"Feels like: {weather_data['feels_like']}°C\n"
                f"Conditions: {weather_data['description']}\n"
                f"Humidity: {weather_data['humidity']}%"
            )
        return "Sorry, I couldn't fetch the weather data at the moment."
    
    if intent == 'calendar':
        try:
            calendar_service = CalendarService()
            # Check if we're creating an event or just viewing
            action = next((entity for entity in entities if entity.get('type') == 'action'), None)
            
            if action and action.get('value') == 'create':
                # Extract event details from entities
                summary = next((entity for entity in entities if entity.get('type') == 'event_name'), None)
                start_time = next((entity for entity in entities if entity.get('type') == 'start_time'), None)
                end_time = next((entity for entity in entities if entity.get('type') == 'end_time'), None)
                
                if not all([summary, start_time, end_time]):
                    return "I need more details to create an event. Please provide the event name, start time, and end time."
                
                return calendar_service.create_event(
                    summary=summary.get('value'),
                    start_time=datetime.fromisoformat(start_time.get('value')),
                    end_time=datetime.fromisoformat(end_time.get('value'))
                )
            else:
                return calendar_service.get_upcoming_events()
                
        except Exception as e:
            logger.error(f"Error handling calendar intent: {str(e)}")
            return "Sorry, I encountered an error while accessing your calendar."
    
    responses = {
        'email': "I'll check your email.",
        'drinking': "I noticed you're talking about drinking. Please be responsible!",
        'unknown': "I'm not sure how to help with that."
    }
    
    return responses.get(intent, "I'm not sure how to help with that.") 