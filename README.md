# BuddyBot

A Flask-based voice assistant that uses OpenAI's GPT-4 to respond to voice commands.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your OpenAI API key
5. Run the application:
   ```bash
   flask run
   ```

## Usage

The assistant responds to "Hey Omi" trigger phrases and processes voice input to generate responses using GPT-4.

## API Endpoints

- `POST /webhook`: Main endpoint for processing voice input
- `GET /webhook/setup-status`: Check setup status
- `GET /status`: Get application status 
