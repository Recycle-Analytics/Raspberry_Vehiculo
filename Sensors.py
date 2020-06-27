#asdsdf
import RPi.GPIO as GPIO, time
import paho.mqtt.client as mqtt
import sys
import time
import datetime
import random

# Pines
GPIO.setmode(GPIO.BCM)
Pin_gas = 18
Pin_fuego = 23
Pin_HumeTemp = 17
DHTPIN = Pin_HumeTemp
#Humedad y temperatura, estado y contadores

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

# Declaramos
broker_address = "aulal.org"
topic_vehiculo = "/vehiculo"
puerto = 1883
Vehiculo = mqtt.Client()
GPIO.setmode(GPIO.BCM)
GPIO.setup(Pin_gas, GPIO.IN)
GPIO.setup(Pin_fuego, GPIO.IN)

def read_dht11_dat():
	GPIO.setup(DHTPIN, GPIO.OUT)
	GPIO.output(DHTPIN, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(DHTPIN, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

	unchanged_count = 0
	last = -1
	data = []
	while True:
		current = GPIO.input(DHTPIN)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1
			if unchanged_count > MAX_UNCHANGE_COUNT:
				break

	state = STATE_INIT_PULL_DOWN

	lengths = []
	current_length = 0

	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
			else:
				continue
		if state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
			else:
				continue
		if state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
			else:
				continue
	if len(lengths) != 40:
		print("...")
		return False

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	print("bits: %s, length: %d" % (bits, len(bits)))
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	print(the_bytes)
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		print("...")
		return False

	return the_bytes[0], the_bytes[2]


#Medicion
try:
    Vehiculo.connect(broker_address)
    Vehiculo.subscribe(topic_vehiculo)
    n  = 10000
    tiempoEncendido = random.randint(0,10)
    vehiculoApagado = 0
    fecha = datetime.date.today()
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    print(hora)
    while True:
        result = read_dht11_dat()
        if result:
	    n+=1
	    if n == vehiculoApagado:
		continue
		print("IdApagado: "+n)
	    estadoVehiculo = 1
	    humidity, temperature = result
	    Humidity = " Humedad: "+str(humidity)+","
            Temperature = " Temperatura: "+str(temperature)+","
	    peso =  random.randint(15000, 18000)
	    VehiculoNum = "IdVehiculo: "+str(n)+","
	    Peso = " Peso(kg): "+ str(peso)+","
	    fecha = datetime.date.today()
	    hora = datetime.datetime.now().strftime("%H:%M:%S")
	    Hora = " Hora: "+ str(hora)+","
	    Fecha = " Fecha: "+ str(fecha)+","
	    if GPIO.input(18):
               	    print("Gas:1")
		    gas = 1
	    else:
		    gas = 0
       	    if GPIO.input(23):
           	    print("Fuego:1")
		    fuego = 1
	    else:
		    fuego = 0
	    if tiempoEncendido == 30:
		vehiculoApagado = n
		estadoVehiculo = 0
		tiempoEncendido = 0
	    Gas = " Gas: "+str(gas)+","
	    Fuego = " Fuego: "+str(fuego)+","
	    EstadoVehiculo = " Encendido: "+str(estadoVehiculo)
	    vehiculo = "{"+VehiculoNum+Fecha+Hora+Peso+Humidity+Temperature + Gas + Fuego + EstadoVehiculo + "}"
	    print(vehiculo)
	    vehiculoPublish = "{"+str(n)+", "+str(fecha)+", "+str(hora)+", "+str(peso)+", "+str(humidity)+", "+str(temperature)+", "+str(gas)+", "+str(fuego)+", "+str(estadoVehiculo)+"}"
	    Vehiculo.publish(topic_vehiculo, vehiculoPublish)
	    if n > 10029:
		n=10000
	    time.sleep(20)
	    tiempoEncendido += 1


# Cierre con except
except KeyboardInterrupt:
    print("ERROR")
    GPIO.cleanup()
