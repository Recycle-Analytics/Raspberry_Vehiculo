import RPi.GPIO as GPIO, time
import paho.mqtt.client as mqtt
import sys
import time
import datetime
import random
import mysql.connector as mariadb
import numpy as np

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

# Declaracion para mqtt.
broker_address = "aulal.org"
topic_vehiculo = "/vehiculo"
puerto = 1883
Vehiculo = mqtt.Client()
GPIO.setmode(GPIO.BCM)
GPIO.setup(Pin_gas, GPIO.IN)
GPIO.setup(Pin_fuego, GPIO.IN)

#Conectar a base de datos.
host = 'berserkit.duckdns.org'
user = 'camion'
password = 'embebidos'
database = 'basuras'
port = 3306
print("Conectando a base de datos...")
mariadb_conexion = mariadb.connect(host=host,port=port,user=user,password=password,database=database)
cursor = mariadb_conexion.cursor()
print("Conectado a MariaDB")
#Func para sensores humedad y temperatura.
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
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		return(False)

	return(the_bytes[0], the_bytes[2])

#Func para extraer rutas:
def datosRutas():
    rutasBdd = cursor.fetchall()
    arrayRutas = np.array([['id_ruta',
			    'IdVehiculo',
			    'contenedores']])
    for datos in rutasBdd:
	idRuta = datos[0]
	IdVehiculo = datos[1]
	contenedores = datos[2]
	arrayRutas = np.append(arrayRutas, [[IdVehiculo,
					     idRuta,
 					     contenedores]],
					     axis=0)
    arrayRutas = np.delete(arrayRutas, 0, axis=0)
    return(arrayRutas)

#Ruta del vehiculo:
def asignacionRuta(n):
    for number in range(len(rutas)):
	IdVehiculo = int(rutas[number][0])
	if IdVehiculo == n:
	    return(rutas[number])

#Medicion.
print("Iniciando toma de datos de sensores...")
try:
    #Conectando a mqtt.
    Vehiculo.connect(broker_address)
    Vehiculo.subscribe(topic_vehiculo)
    #IdVehiculo.
    n  = 10001
    #OnOff.
    tiempoEncendido = random.randint(0,10)
    vehiculoApagado = 0
    #Se toman los valores de la bdd.
    cursor.execute("SELECT id_ruta, IdVehiculo, contenedores  FROM rutas")
    rutas = datosRutas()
    print(rutas)
    #Inicia medicion.
    while True:
        result = read_dht11_dat()
        if result:
	    if n > 10030:
                n=10001
	    estadoVehiculo = 1
	    ruta = asignacionRuta(n)
	    print(ruta, n)
	    if ruta is None:
		print("Vehiculo "+str(n)+" sin ruta asignada")
		n+=1
		continue
	    #Verificacion del estado del vehiculo.
	    if n == vehiculoApagado:
		print("ID apagado: " + str(n))
		n+=1
		continue
	    #Medicion de fuego y gas.
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
	    #Vehiculo que se apagara.
            if tiempoEncendido == 30:
                vehiculoApagado = n
                estadoVehiculo = 0
                tiempoEncendido = 0
	    #Medicion y organizacion de los datos. Humedad y Temperatura.
	    humidity, temperature = result
	    Humidity = " Humedad: "+str(humidity)+","
            Temperature = " Temperatura: "+str(temperature)+","
	    #Peso.
	    peso =  random.randint(15000, 18000)
	    Peso = " Peso(kg): "+ str(peso)+","
	    #IdVehiculo.
	    VehiculoNum = "IdVehiculo: "+str(n)+","
	    #Fecha y hora de medicion.
	    fecha = datetime.date.today()
	    hora = datetime.datetime.now().strftime("%H:%M:%S")
	    Hora = " Hora: "+ str(hora)+","
	    Fecha = " Fecha: "+ str(fecha)+","
	    #Gas-Fuego.
	    Gas = " Gas: "+str(gas)+","
	    Fuego = " Fuego: "+str(fuego)+","
	    #Vehiculo OnOff.
	    EstadoVehiculo = " Encendido: "+str(estadoVehiculo)
	    vehiculo = "{"+VehiculoNum+Fecha+Hora+Peso+Humidity+Temperature + Gas + Fuego + EstadoVehiculo + "}"
	    print(vehiculo)
	    #Publicacion de datos por mqtt.
	    vehiculoPublish = "{"+str(n)+", "+str(fecha)+", "+str(hora)+", "+str(peso)+", "+str(humidity)+", "+str(temperature)+", "+str(gas)+", "+str(fuego)+", "+str(estadoVehiculo)+"}"
	    Vehiculo.publish(topic_vehiculo, vehiculoPublish)
	    #Limite de Vehiculos.
	    print("Esperando datos del siguiente vehiculo...")
	    time.sleep(20)
	    tiempoEncendido += 1
	    n+=1


# Cierre con except
except KeyboardInterrupt:
    print("ERROR")
    GPIO.cleanup()
