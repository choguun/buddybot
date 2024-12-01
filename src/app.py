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
    if request.method == 'POST':
        logger.info("Received webhook POST request")
        data = request.json
        logger.info(f"Received data: {data}")
        
        session_id = data.get('session_id')
        if not session_id:
            logger.error("No session_id provided in request")
            return jsonify({"status": "error", "message": "No session_id provided"}), 400
            
        segments = data.get('segments', [])
        logger.info(f"Processing session_id: {session_id}, number of segments: {len(segments)}")
        
        current_time = time.time()
        buffer_data = message_buffer.get_buffer(session_id)
        
        # Process segments and check for triggers
        for segment in segments:
            if not segment.get('text'):
                continue
                
            text = segment['text'].lower().strip()
            logger.info(f"Processing text segment: '{text}'")
            
            # Check for trigger phrases
            if any(trigger in text for trigger in TRIGGER_PHRASES):
                # Analyze the intent of the message
                intent_data = analyze_intent(text)
                response = get_intent_response(intent_data)
                
                # Log the intent analysis
                logger.info(f"Intent analysis for session {session_id}: {intent_data}")
                
                return jsonify({
                    "message": response,
                    "intent_data": intent_data
                }), 200
        
        return jsonify({"status": "success"}), 200

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
def setup_status():
    return jsonify({
        "status": "OK",
        "message": "Enable and enjoy! Just ask your questions and I'll do my best to answer them."
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)