import os
from google import genai
import re 
from dotenv import load_dotenv
import random
import time
import paho.mqtt.client as mqtt
from print_color import print

load_dotenv()

time_between_actions = 20
time_between_loop = 20

stored_readings = {}
received_first_readings = False

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
    print("Connected to broker with result code " + str(rc))

    # Subscribe to sensor topics
    mqtt_client.subscribe("sensors/light")
    mqtt_client.subscribe("sensors/moisture")
    mqtt_client.subscribe("sensors/temp")

def on_message(client, userdata, msg):
    global received_first_readings
    if received_first_readings == False:
        received_first_readings = True
    
    #print(f"[{msg.topic}] {msg.payload.decode()}")
    #here we store the last value received for each topic
    topic = msg.topic
    payload = msg.payload.decode()
    stored_readings[topic] = payload

 
print("Starting MQTT Connection", tag="System", tag_color="green", color="white")
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
mqtt_client.username_pw_set(mqtt_user, mqtt_pass)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(mqtt_broker, mqtt_port, 60)
mqtt_client.loop_start()

# extract the tool call from the response
def extract_tool_call(text):
    import io
    from contextlib import redirect_stdout
 
    pattern = r"```tool_code\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        
        allowed_functions = ['get_temperature', 'get_soil_moisture', 'toggle_grow_lamp', 'water_plant', 'get_light_reading']
        is_safe = False
        
        for func in allowed_functions:
            if code.startswith(func):
                is_safe = True
                break
        
        if is_safe:
            result = eval(code)
        else: 
            print("Code does not match predetermined functions.")
            return None
            
        r = result
        return f'```tool_output\n{r}\n```'''
    
    else:
        return None

## TODO:
## Get time
##Get lamp status
    
def get_temperature() -> float:
  print("Getting temperature 🌡️")
  #simulated_temp = random.randrange(5, 30, 1)
  curr_temp = float(stored_readings.get("sensors/temp"))
  mqtt_client.publish("overview/status", "Getting temperature 🌡️")
  return  curr_temp

def get_soil_moisture() -> float:
  print("Getting soil moisture 💦")
  curr_moisture = float(stored_readings.get("sensors/moisture"))
  mqtt_client.publish("overview/status", "Getting soil moisture 💦")
  return  curr_moisture

def get_light_reading() -> float:
  print("Getting light reading 🔦")
  curr_light = float(stored_readings.get("sensors/light"))
  mqtt_client.publish("overview/status", "Getting light reading 🔦")
  
  return  curr_light

#actually maybe i should return success or failure codes here
def toggle_grow_lamp(state: bool) -> str:
    print("Sending Lamp Toggle")
    if state == True:
        print("Turning Lamp On 🌕")
        mqtt_client.publish("commands/relay1", "on")
        mqtt_client.publish("overview/status", "Setting light on 🌕")
    else:
        print("Turning Lamp Off 🌑")
        mqtt_client.publish("commands/relay1", "off")
        mqtt_client.publish("overview/status", "Setting light off 🌑")

    return "DONE"

def water_plant(duration: float) -> str:
    print(f"Watering plant for {duration} seconds 🌧️")
    mqtt_client.publish("commands/relay2", duration)
    mqtt_client.publish("overview/status", "Watering Plants 🌧️")
    return "DONE"

####To do 
#- add Time - we also want to simulate natural rythym of light
# add checking light level with photodiode

instruction_prompt_with_function_calling = '''You are in charge of taking care of a plant (African bird's eye chili). Water first. At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used. You may only choose one function per turn.

The following Python methods are available:

```python
def get_temperature() -> float:
    """Get the latest measured temperature in °C
    """

def get_soil_moisture() -> float:
    """Get the moisture level of the plant's soil ranging from 4095 (dry or malfunctioning) to 1800 (soaking)
    """    

def get_light_reading() -> float:
    """Get the light level in the room - 0 (Extremely bright) to 10 (very dark)
    """    

def toggle_grow_lamp(state: bool) -> string:
    """Turn the lamp on or off. Result is "ON" or "OFF" confirmation.

    Args:
        state: true for on and false for off
    """

def water_plant(duration: float) -> string:
"""Water the plant. It flows at 25ml/sec.
   Returns 'DONE' for command received.

Args:
    duration: how long to water for
"""

```

User: {user_message}
'''

chat = client.chats.create(model=model_id)

while received_first_readings == False:
    print("Waiting for first values", tag="System Init", tag_color="red",color="white")
    time.sleep(5)


#Telling Gemma to check the Plant
response = chat.send_message(instruction_prompt_with_function_calling.format(user_message="Time to check on the plant"))
print(response.text,  tag="Gemma", tag_color='blue', color='white')
print("------------------------------------------------------")
#Extract tool and run command
call_response = extract_tool_call(response.text)
print(call_response, tag="Result", tag_color='green', color='white')
print("------------------------------------------------------")
time.sleep(time_between_actions) 

while True:
    
    #Give Gemma the FeedbacK
    if call_response is not None:
        response = chat.send_message(call_response)
        print(response.text,  tag="Gemma", tag_color='blue', color='white')
        print("------------------------------------------------------")
    else: 
        response = chat.send_message("Check on the plant")
        print(response.text,  tag="Gemma", tag_color='blue', color='white')
        print("------------------------------------------------------")
    #Extract tool and run command
    call_response = extract_tool_call(response.text)
    time.sleep(time_between_actions) 
    if call_response is not None:
        #Give Gemma the FeedbacK
        response = chat.send_message(call_response)
        print(response.text,  tag="Gemma", tag_color='blue', color='white')
        print("------------------------------------------------------")

    call_response = extract_tool_call(response.text)
    time.sleep(time_between_actions) 
    
    if call_response is not None:
        response = chat.send_message(call_response)
        print(response.text,  tag="Gemma", tag_color='blue', color='white')
        print("------------------------------------------------------")

        call_response = extract_tool_call(response.text)
    
    #-> Then start the loop again
    time.sleep(time_between_loop) 
 
