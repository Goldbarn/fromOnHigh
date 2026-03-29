import requests
import json

class AIPlayer:
    def __init__(self, model="llama3.2:latest"):
        self.model = model
        self.url = "http://127.0.0.1:11434/api/generate"

    def get_decision(self, current_hex, grid):
        prompt = f"""
Tribe at q:{current_hex.q}, r:{current_hex.r}. Action: move (1 space away) or found_city.
Return ONLY JSON. Ex: {{"action": "move", "q": {current_hex.q+1}, "r": {current_hex.r}}} OR {{"action": "found_city"}}
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

    def get_unit_decision(self, state):
        prompt = f"""
{state['unit_type']} unit at q:{state['q']}, r:{state['r']}.
Surroundings: {state['surroundings']}
Other cities: {state['other_cities']}"""

        if state.get('god_whisper'):
            prompt += f"\n\nThe Gods command you (prioritize this): {state['god_whisper']}"
            
        if state.get('last_failure'):
            prompt += f"\n\nWARNING: Your last action failed! Reason: {state['last_failure']}. Choose a DIFFERENT, valid action."
        
        prompt += "\nReturn ONLY JSON."

        if state['unit_type'] == "army":
            prompt += """\nActions: "move" (adj hex) or "guard". Ex: {"action": "move", "q": 1, "r": 0} or {"action": "guard"}"""
        else:
            prompt += """\nActions: "move" (adj hex) or "settle". Ex: {"action": "move", "q": 1, "r": 0} or {"action": "settle"}"""
            
        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
        
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            if response.status_code == 200:
                return json.loads(response.json()['response'])
        except Exception as e:
            print(f"AI Connection Error: {e}")
        return {}

    def get_city_decision(self, state):
        prompt = f"""
Leader. Personality: {state['personality']}
Wealth: {state['wealth']} | Res: {state['resources']} | Resrch: {state['research']}
Surroundings: {state['surroundings']}
Costs: army(1 creature), settler(2 water), farm(1 earth), mine(1 stone), institute(1 metal + 1 fire), msg(1 wind), trade(3 of same resource to get 1 random other resource), condense(2 light or 2 dark to get 1 other)
Actions:
- "train_army"
- "train_settler"
- "build_farm" (on plant/creature/water)
- "build_mine" (not on ice)
- "build_institute"
- "trade" (add "give" element field)
- "condense" (add "give" and "get" element fields)
- "pray"
- "send_message" (add "message" field)
Only choose an action if you have the required resources."""

        if state.get('god_whisper'):
            prompt += f"\n\nThe Gods command you (prioritize this): {state['god_whisper']}"

        if state.get('last_failure'):
            prompt += f"\n\nWARNING: Your last action failed! Reason: {state['last_failure']}. Choose a DIFFERENT, valid action."

        prompt += """\nReturn ONLY JSON. Ex: {"action": "train_army"}"""
        
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