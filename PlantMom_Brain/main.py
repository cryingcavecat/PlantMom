import os
from google import genai
import re 
from dotenv import load_dotenv
import random
import time
import paho.mqtt.client as mqtt


#Some escaape char for colours
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


load_dotenv()

# MQTT stuff
mqtt_user = os.getenv('MQTT_USER',"Couldn't find MQTT username")
mqtt_pass =  os.getenv('MQTT_PASS',"Couldn't find MQTT password")
mqtt_broker = "192.168.0.199" #"localhost" 
mqtt_port = 1883

# GenAI stuff 
api_key = os.getenv('GEMINI_API_KEY',"Couldn't find API Key")
client = genai.Client(api_key=api_key)
# speicfy the model id
model_id = "gemma-3-27b-it"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribe to sensor topics
    mqtt_client.subscribe("sensors/light")
    mqtt_client.subscribe("sensors/moisture")

def on_message(client, userdata, msg):
    print(f"[{msg.topic}] {msg.payload.decode()}")

 

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(mqtt_user, mqtt_pass)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(mqtt_broker, mqtt_port, 60)


# extract the tool call from the response
def extract_tool_call(text):
    import io
    from contextlib import redirect_stdout
 
    pattern = r"```tool_code\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        # Capture stdout in a string buffer
        f = io.StringIO()
        with redirect_stdout(f):
            result = eval(code)
        output = f.getvalue()
        r = result if output == '' else output
        return f'```tool_output\n{r}\n```'''
    return None

    
def get_temperature() -> float:
  simulated_temp = random.randrange(5, 30, 1)
  return  simulated_temp

def get_soil_moisture() -> float:
  simulated_moisture = random.randrange(0, 100, 1)
  return  simulated_moisture

#actually maybe i should return success or failure codes here
def toggle_grow_lamp(state: bool) -> str:
    print("Sending Lamp Toggle")
    if state == true:
        mqtt_client.publish("commands/relay1", "on")
    else:
        mqtt_client.publish("commands/relay1", "off")

    return "DONE"

def water_plant(duration: float) -> str:
    print("Sending Water Pump Command")
    mqtt_client.publish("commands/relay2", duration)
    return "DONE"

####To do 
#- add Time - we also want to simulate natural rythym of light
# add checking light level with photodiode

instruction_prompt_with_function_calling = '''You are in charge of taking care of a plant: watering it and adjusting the light. At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used. You may only choose one function per turn.

The following Python methods are available:

```python
def get_temperature() -> float:
    """Get the latest measured temperature in °C
    """

def get_soil_moisture() -> float:
    """Get the moisture level of the plant's soil ranging from 0 (dry) to 100 (soaking)
    """    

def toggle_grow_lamp(state: bool) -> string:
    """Turn the lamp on or off. Result is "ON" or "OFF" confirmation.

    Args:
        state: true for on and false for off
    """

def water_plant(duration: float) -> string:
"""Water the plant. It flows at 100ml/5 seconds.
   Returns 'DONE' for command received.

Args:
    duration: how long to water for
"""

```

User: {user_message}
'''

chat = client.chats.create(model=model_id)

while True:
    #Telling Gemma to check the Plant
    response = chat.send_message(instruction_prompt_with_function_calling.format(user_message="Time to check on the plant"))
    print(f"{bcolors.OKBLUE}{response.text}{bcolors.RESET}")
    time.sleep(60) 
    #Extract tool and run command
    call_response = extract_tool_call(response.text)
    print("Running")
    print(call_response)
    time.sleep(60) 
    #Give Gemma the FeedbacK
    response = chat.send_message(call_response)
    print(f"{bcolors.OKBLUE}{response.text}{bcolors.RESET}")
    time.sleep(60)
    #Extract tool and run command
    call_response = extract_tool_call(response.text)
    time.sleep(5)
    #-> Then start the loop again
