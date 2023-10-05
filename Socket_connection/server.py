import socket
import json
import random
import time


####-----Creates Socket, Binds port, Start listening incoming connections-----#####

s = socket.socket()
print("Socket Created")
s.bind(('',12345))
s.listen(3)
print("waiting for connections")
c, addr = s.accept()


# data =[{
#     "Battery_Level":3.52,
#     "Device_Id":1156053076,
#     "First_Sensor_temperature":19.4 ,
#     "Route_From":"Hyderabad, India",
#     "Route_To":"Louisville, USA"
#     },
#     {
#     "Battery_Level":2.57,
#     "Device_Id":1156053077,
#     "First_Sensor_temperature":20.4 ,
#     "Route_From":"Banglore, India",
#     "Route_To":"Louisville, USA"
#     }]

connected = True

####-----Sending Device data in JSON format-----#####

while connected:
    try:
        print("connected with", addr)
        routefrom = random.choice(["Mumbai, India", "Chennai, India", "Hyderabad, India", "Bangalore, India"])
        routeto = random.choice(["Louisville, USA", "San Franciso, USA", "Mumbai, India", "Chennai, India"])
        if(routefrom!=routeto):
            data = [{
                "Battery_Level":round(random.uniform(2.00,5.00),2),
                "Device_Id": random.randint(11560533076,11560533077),
                "First_Sensor_temperature":round(random.uniform(19.0,24.0),1),
                "Route_From":routefrom,
                "Route_To":routeto
                }]
        else:
            continue

        # print("connected with", addr)
        userdata = (json.dumps(data)+"\n").encode('utf-8')
        print(userdata)
        c.send(userdata)
        time.sleep(5)  
        #Sends the encoded data over the socket connection to client and waits for 5 seconds before the next iteration.
            

    except Exception as e:
        print(e)
c.close()