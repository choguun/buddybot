from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
import datetime
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar.events']

class CalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.initialize_credentials()

    def initialize_credentials(self):
        """Initialize or load credentials for Google Calendar API"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('calendar', 'v3', credentials=self.creds)

    def get_upcoming_events(self, max_results=5):
        """Get upcoming calendar events"""
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "No upcoming events found."
                
            response = "Upcoming events:\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                response += f"- {event['summary']} on {start_dt.strftime('%Y-%m-%d %H:%M')}\n"
                
            return response

        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}")
            return "Sorry, I couldn't fetch your calendar events at the moment."

    def create_event(self, summary, start_time, end_time, description=None):
        """Create a new calendar event"""
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if description:
                event['description'] = description

            event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            return f"Event created: {event.get('htmlLink')}"

        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return "Sorry, I couldn't create the calendar event." 