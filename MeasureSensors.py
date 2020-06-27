import RPi.GPIO as GPIO, time
import paho.mqtt.client as mqtt
import sys

# Declaramos
broker_address = "aulal.org"
topic_gas = "/gas"
topic_fuego = "/fuego"
puerto = 1883
Gas = mqtt.Client()
Fuego = mqtt.Client()
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(23, GPIO.IN)
#codigo
try:
    Gas.connect(broker_address)
    Gas.subscribe(topic_gas)
    Fuego.connect(broker_address)
    Fuego.subscribe(topic_fuego)
    while True:
        if GPIO.input(18):
        	print("Gas")
        	time.sleep(0.2)
		Gas.publish(topic_gas, "{Gas:1}")
	if GPIO.input(23):
		print("Fuego")
		time.sleep(0.2)
		Fuego.publish(topic_fuego, "{Fuego:1}")
        if GPIO.input(18)!=1 and GPIO.input(23)!=1:
        	print("Gas:0 and Fuego:0")
        	time.sleep(0.2)
		Gas.publish(topic_gas, "{Gas:0}")
		Fuego.publish(topic_fuego, "{Fuego:0}")

# Cerramos el script
except KeyboardInterrupt:
    print "ERROR"
    GPIO.cleanup()
