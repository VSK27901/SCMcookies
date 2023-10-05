import socket
import json
import os
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

###----Create Socket Connection----###

socket_conn = socket.socket()


host=os.getenv("host")
port = int(os.getenv("port"))

server_address = (host, port)
socket_conn.connect(server_address)

###----Configure Kafka Producer----###

bootstrap_servers =os.getenv("bootstrap_servers")  

topic_name=os.getenv("topic_name")

producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                            value_serializer=lambda m: json.dumps(m).encode('utf-8'), api_version=(0, 11, 5))

while True:
    try:

        data = socket_conn.recv(4096)
        if not data:
            break

        data = json.loads(data.decode('utf-8')) 
        # print(data)

        producer.send(topic_name, value=data)

    except Exception as e:
        print("Error:", e)
        break

producer.close()
socket_conn.close()
