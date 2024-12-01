from flask import Flask, request, jsonify
import logging
import time
from collections import defaultdict
from src.models.message_buffer import MessageBuffer
from src.services.openai_service import get_openai_response
from src.config import (
    TRIGGER_PHRASES, PARTIAL_FIRST, PARTIAL_SECOND,
    QUESTION_AGGREGATION_TIME, NOTIFICATION_COOLDOWN,
    PORT, DEBUG
)
from src.services.intent_analyzer import analyze_intent, get_intent_response
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
start_time = time.time()

# Initialize message buffer and cooldowns
message_buffer = MessageBuffer()
notification_cooldowns = defaultdict(float)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        logger.info(f"Received webhook data: {data}")
        
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"status": "error", "message": "No session_id provided"}), 400
        
        segments = data.get('segments', [])
        if not segments:
            return jsonify({"status": "success", "message": "No segments to process"}), 200
        
        current_time = time.time()
        buffer_data = message_buffer.get_buffer(session_id)
        
        # Check cooldown
        if buffer_data['trigger_detected']:
            time_since_last = current_time - notification_cooldowns[session_id]
            if time_since_last < NOTIFICATION_COOLDOWN:
                logger.debug(f"Cooldown active for {session_id}, {NOTIFICATION_COOLDOWN - time_since_last:.1f}s remaining")
                return jsonify({"status": "success", "message": "Cooldown active"}), 200
        
        for segment in segments:
            text = segment.get('text', '').lower().strip()
            if not text:
                continue
                
            logger.debug(f"Processing segment: '{text}' for session {session_id}")
            
            # Check for complete trigger
            if any(trigger in text for trigger in TRIGGER_PHRASES):
                buffer_data['trigger_detected'] = True
                buffer_data['trigger_time'] = current_time
                buffer_data['collected_question'] = []
                notification_cooldowns[session_id] = current_time
                
                # Extract question after trigger
                for trigger in TRIGGER_PHRASES:
                    if trigger in text:
                        question_part = text.split(trigger)[-1].strip()
                        if question_part:
                            buffer_data['collected_question'].append(question_part)
                        break
                continue
            
            # Handle partial triggers
            if not buffer_data['trigger_detected']:
                if handle_partial_trigger(text, buffer_data, current_time):
                    continue
            
            # Collect question if trigger is active
            if buffer_data['trigger_detected'] and not buffer_data['response_sent']:
                time_since_trigger = current_time - buffer_data['trigger_time']
                
                # Add to question collection
                if time_since_trigger <= QUESTION_AGGREGATION_TIME:
                    buffer_data['collected_question'].append(text)
                
                # Check if we should process the question
                if should_process_question(buffer_data, time_since_trigger, text):
                    response = process_question(buffer_data)
                    message_buffer.reset_buffer(session_id)
                    return jsonify({"message": response}), 200
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

def handle_partial_trigger(text, buffer_data, current_time):
    """Handle partial trigger detection"""
    if any(text.endswith(part) for part in PARTIAL_FIRST):
        buffer_data['partial_trigger'] = True
        buffer_data['partial_trigger_time'] = current_time
        return True
        
    if buffer_data['partial_trigger']:
        time_since_partial = current_time - buffer_data['partial_trigger_time']
        if time_since_partial <= 2.0 and any(part in text for part in PARTIAL_SECOND):
            buffer_data['trigger_detected'] = True
            buffer_data['trigger_time'] = current_time
            buffer_data['collected_question'] = []
            return True
    return False

def should_process_question(buffer_data, time_since_trigger, text):
    """Determine if question should be processed"""
    return (
        buffer_data['collected_question'] and (
            time_since_trigger > QUESTION_AGGREGATION_TIME or
            '?' in text or
            time_since_trigger > QUESTION_AGGREGATION_TIME * 1.5
        )
    )

def process_question(buffer_data):
    """Process collected question and get response"""
    full_question = ' '.join(buffer_data['collected_question']).strip()
    if not full_question.endswith('?'):
        full_question += '?'
    
    logger.info(f"Processing question: {full_question}")
    return get_openai_response(full_question)

@app.route('/webhook/setup-status', methods=['GET'])
def setup_status():
    return jsonify({
        "status": "OK",
        "message": "Webhook setup is complete and ready to receive requests."
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "active_sessions": len(message_buffer.buffers),
        "uptime": time.time() - start_time
    })

@app.route('/instructions', methods=['GET'])
def instructions():
    return jsonify({
        "status": "OK",
        "message": "Enable and enjoy! Just ask your questions and I'll do my best to answer them."
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)