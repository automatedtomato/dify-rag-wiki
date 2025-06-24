import requests
import os
import json

from logging import getLogger
from backend.app.common.log_setter import setup_logger
from backend.app.common.config_loader import load_config


# ========== Constants ==========
# Intra connection between containers: designate "api" container
DIFY_API_URL = "http://api:5001/v1"

DIFY_API_KEY = os.getenv("DIFY_API_KEY")

# ========== Logging Config ==========
logger = getLogger(__name__)
config = load_config(layer="logger")
logger = setup_logger(logger=logger, config=config)

# ========== Dify API Client Class ==========
class DifyClient:
    def get_headers(self):
        return {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
    def chat(self, user_input: str, user_id: str, conversation_id: str | None = None):
        """
        Call Diy chat-messages API and get response in stream
        
        Args:
            user_input (str): User input
            session_id (str): Session ID
        """
        
        url = f"{DIFY_API_URL}/chat-messages"
        
        payload = {
            "inputs": {},
            "query": user_input,
            "user": user_id, # To track user, use session_id
            "response_mode": "streaming"
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
            
        try:
            response = requests.post(
                url=url,
                headers=self.get_headers(),
                json=payload,
                stream=True
                )
            
            response.raise_for_status()
            
            # Process response line by line
            final_answer = ""
            dify_conversation_id = None
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data:"):
                        # remove "data:"
                        json_str = decoded_line[len("data:"):].strip()
                        try:
                            data = json.loads(json_str)
                            # Extract response field from 'agent_message' or 'message' event
                            if data.get("event") in ["agent_message", "message"]:
                                final_answer += data.get("answer", "")
                                
                            if data.get("event") == "message_end":
                                dify_conversation_id = data.get("conversation_id")
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON: {decoded_line}")
                            continue
                        
            return final_answer, dify_conversation_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Dify API: {e}")
            if e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
            return None, None