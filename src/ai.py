import requests
import json

class AIPlayer:
    def __init__(self, model="llama3.2:latest"):
        self.model = model
        self.url = "http://127.0.0.1:11434/api/generate"

    def get_decision(self, current_hex, grid):
        # Simple prompt instructing Ollama to act as a tribe and return JSON
        prompt = f"""
        You are a primitive tribe in a hex-grid game. 
        You are currently at coordinates q: {current_hex.q}, r: {current_hex.r}.
        
        You can choose to explore by moving, or build your city.
        If you move, pick coordinates exactly 1 space away (e.g., q+1 or r+1, etc).
        
        Respond ONLY with a valid JSON object. Do not include any other text.
        
        To move, use this format: {{"action": "move", "q": {current_hex.q}, "r": {current_hex.r + 1}}}
        To build your city, use this format: {{"action": "found_city"}}
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return json.loads(result['response'])
        except Exception as e:
            print(f"AI Connection Error: {e}")
        return {} # Return empty dict if something fails so the game can retry

    def get_city_decision(self, state):
        prompt = f"""
        You are the leader of a surviving human tribe in a ruined, hex-grid world.
        Your tribe's personality: {state['personality']}
        
        Current Status:
        - Food: {state['food']}
        - Wind Resources (Used for messaging): {state['wind']}
        - Research Level: {state['research']}
        
        Surrounding Terrain: {state['surroundings']}
        
        Choose ONE action to ensure your survival or please the Ascended (the Gods):
        - "train_army": Defend yourself or expand.
        - "build_mine": Gather resources from your terrain.
        - "build_institute": Advance your technology.
        - "pray": Beg the Gods for mercy, blessings, or food.
        - "send_message": Costs 1 Wind. (If you choose this, include a "message" field in your JSON).
        
        Respond ONLY with a valid JSON object. Do not include any other text.
        Example 1: {{"action": "build_mine"}}
        Example 2: {{"action": "send_message", "message": "We seek an alliance."}}
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            if response.status_code == 200:
                return json.loads(response.json()['response'])
        except Exception as e:
            print(f"AI Connection Error: {e}")
        return {}