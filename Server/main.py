# import paho.mqtt.client as mqtt
# import json
# from datetime import datetime
# from collections import deque
# import numpy as np


# # MQTT Broker settings
# BROKER = "broker.hivemq.com"
# PORT = 1883
# #BASE_TOPIC = "ENTER_SOMETHING_UNIQUE_HERE_THAT_SHOULD_ALSO_MATCH_MAINCPP/ece140/sensors"
# BASE_TOPIC = "chynson/ece140/sensors"
# TOPIC = BASE_TOPIC + "/#"

# if BASE_TOPIC == "ENTER_SOMETHING_UNIQUE_HERE_THAT_SHOULD_ALSO_MATCH_MAINCPP/ece140/sensors":
#     print("Please enter a unique topic for your server")
#     exit()


# def on_connect(client, userdata, flags, rc):
#     """Callback for when the client connects to the broker."""
#     if rc == 0:
#         print("Successfully connected to MQTT broker")
#         client.subscribe(TOPIC)
#         print(f"Subscribed to {TOPIC}")
#     else:
#         print(f"Failed to connect with result code {rc}")

# def on_message(client, userdata, msg):
#     """Callback for when a message is received."""
    
#     # Print received message to debug
#     print(f" Received message on topic: {msg.topic}")
#     print(f" Raw Payload: {msg.payload.decode()}")  # Debugging step

#     try:
#         # Parse JSON message
#         payload = json.loads(msg.payload.decode())
#         current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         if msg.topic == BASE_TOPIC + "/readings":
#             hall_value = payload.get("hall", "N/A")
#             temperature = payload.get("temperature", "N/A")

#             print(f" [{current_time}] Received sensor data:")
#             print(f"    Hall Value: {hall_value}")
#             print(f"    Temperature: {temperature}°C\n")
#         else:
#             print(f"⚠️ [{current_time}] Unexpected topic: {msg.topic}, Payload: {payload}")

#     except json.JSONDecodeError:
#         print(f" JSON Decode Error on {msg.topic}:")
#         print(f" Raw Payload: {msg.payload.decode()}")


  
        
# def main():
#     # Create MQTT client
#     print("Creating MQTT client...")
#     client = mqtt.Client()

#     # Set the callback functions onConnect and onMessage
#     print("Setting callback functions...")
#     client.on_connect = on_connect
#     client.on_message = on_message
#     try:
#         # Connect to broker
#         print("Connecting to broker...")
#         client.connect(BROKER, PORT, 60)
#         # Start the MQTT loop
#         print("Starting MQTT loop...")
#         client.loop_forever()
#     except KeyboardInterrupt:
#         print("\nDisconnecting from broker...")
#         # make sure to stop the loop and disconnect from the broker
#         print("Exited successfully")
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     main()



import paho.mqtt.client as mqtt
import json
import requests
import time
from dotenv import load_dotenv
import os
from datetime import datetime


load_dotenv()
BASE_TOPIC = os.getenv("BASE_TOPIC", "chynson/ece140/sensors")  # Default value if not set
# WEB_SERVER_URL = "http://localhost:8000/api/temperature"
WEB_SERVER_URL = "https://depolyed-fit.onrender.com/api/temperature"

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = BASE_TOPIC + "/#"


last_request_time = 0

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print(" Successfully connected to MQTT broker")
        client.subscribe(TOPIC)
        print(f" Subscribed to {TOPIC}")
    else:
        print(f" Failed to connect with result code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received."""
    global last_request_time  # Track last request time

    print(f" Received message on topic: {msg.topic}")
    print(f" Raw Payload: {msg.payload.decode()}")  

    try:
       
        payload = json.loads(msg.payload.decode())
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if msg.topic == BASE_TOPIC + "/readings":
            temperature = payload.get("temperature")
            
            if temperature is not None:
                print(f" [{current_time}] Temperature Received: {temperature}°C")

                
                if time.time() - last_request_time >= 5:
                    
                    data = {
                        "value": temperature,  
                        "unit": "Celsius",     
                        "timestamp": current_time
                    }

                    
                    try:
                        response = requests.post(WEB_SERVER_URL, json=data)
                        if response.status_code == 200:
                            print(f" Data sent to web server successfully: {response.json()}")
                        else:
                            print(f"⚠️ Failed to send data. Server responded with: {response.status_code} - {response.text}")
                    except requests.RequestException as e:
                        print(f" Error sending data to web server: {e}")

                    
                    last_request_time = time.time()
                else:
                    print(" Skipping request to prevent flooding (waiting 5 seconds).")
            else:
                print(" No temperature data found in payload.")

        else:
            print(f" Unexpected topic: {msg.topic}, Payload: {payload}")

    except json.JSONDecodeError:
        print(f" JSON Decode Error on {msg.topic}:")
        print(f"Raw Payload: {msg.payload.decode()}")


def main():
    """Main function to start the MQTT client."""
    print(" Creating MQTT client...")
    client = mqtt.Client()

    print("⚙️ Setting callback functions...")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(" Connecting to broker...")
        client.connect(BROKER, PORT, 60)

        print(" Starting MQTT loop...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n Disconnecting from broker...")
        print(" Exited successfully")
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    main()