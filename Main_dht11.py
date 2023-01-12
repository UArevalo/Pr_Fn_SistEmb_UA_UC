#Author Unai Arevalo & Unai Chasco
#Curso 2022/2023 Sistemas Embebidos. Universidad de Deusto
# ------------------------------------------------


#Se importan las librerías necesarias 
import RPi
import RPi.GPIO as GPIO
import smbus
import time
import datetime

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


#Inicialización de las variables de la pantalla
bus = smbus.SMBus(1)
i2c_adress = 0x3e

#Función que escribe la variable "text" en la pantalla
def setText(text):
    bus.write_byte_data(i2c_adress,0x80,0x02) # comando CURSOR RETURN
    time.sleep(.05)
    bus.write_byte_data(i2c_adress,0x80,0x08 | 0x04)# display on, no cursor
    bus.write_byte_data(i2c_adress,0x80,0x28) # 2 lineas
    time.sleep(.05)
    count = 0
    row = 0
    while len(text) < 32: 
        text += ' ' #Rellenar (anadir al final) con caracter vacio ' ' hasta llegar al tope que admite de 32 caracteres
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            bus.write_byte_data(i2c_adress,0x80,0xc0) #cambiar a la segunda linea 
            if c == '\n':
                continue
        count += 1
        character_unicode = ord(c)
        bus.write_byte_data(i2c_adress,0x40,character_unicode)

class DHT11:
    pin = 5

    def __init__(self, pin):
        self.pin = pin

    def read(self):

        #PASO 1: PULSO DE START
        #----------------------
        #GPIO OUTPUT
        RPi.GPIO.setup(self.pin, RPi.GPIO.OUT)

        # Enviar HIGH inicial
        RPi.GPIO.output(self.pin, RPi.GPIO.HIGH)
        time.sleep(0.05)

        # ENVIAR LOW (debes ser >18ms)
        RPi.GPIO.output(self.pin, RPi.GPIO.LOW)
        time.sleep(0.02)
  
        # #GPIO OUTPUT - PULLUP RESISTOR
        RPi.GPIO.setup(self.pin, RPi.GPIO.IN, RPi.GPIO.PUD_UP)
        
        
        #PASO 2: GUARDAMOS LOS PULSOS RECIBIDOS 
        #--------------------------------------------------
        # Leer estados del pin
        data = self.get_data()

        #PASO 3: CALCULAMOS LA DURACION DE LOS PULSOS  (en ciclos)  
        #---------------------------------------------------------
        # Calcular el numero de 0s y 1s de cada pulso (tamanos de los pulsos alto y bajo)
        data_lengths = self.parse_data(data)

        # Error: numero de bits recibidos erroneos (segun datasheet 40 bits totaltes)
        if len(data_lengths) != 40:
            print("ERROR: numero de bits recibidos: "+str(data_lengths))
            return -1,-1

        #Calcular bits a partir del tamano de los pulsos alto y bajo
        #---------------------------------------------------------
        bits = self.calculate_bits(data_lengths)
        print("Formato de bits: "+str(bits))


        #**************************************************************
        # A partir de los bits, calcular los bytes (grupos de 8 bits)
        # ESTO TENEIS QUE IMPLEMENTARLO
        #**************************************************************
        byts = []
        size=8
        for i in range(0, len(bits), size):
            byte = bits[i:i + size]
            byts.append(byte)
        
        
        num = []
        
        for b in byts:
            index = 7
            n=0
            for bit in b:
                n=n + (bit*(2**(index)))
                index= index-1
            num.append(n)   
        
        #**************************************************************
        # COMPROBAR QUE EL CHECKSUM ES CORRECTO
        # EN CASO DE NO SERLO, IMPRIMIR ERROR check cum es la suma de los 4 primeros bytes
        #**************************************************************
        checksum= num[0]+ num[1]+num[2]+num[3]
        if checksum == num[4]:
            print("Lectura buena")
            temperature = num[0] + (num[1]/10)
            humidity = num[2]+ (num[3]/10)
        else:
            print("Lectura mala")
            temperature = 0
            humidity = 0

        return temperature, humidity




#leer estados de los pines hasta que la senal no cambie en un periodo de unos
# 100 pulsos. La transmision de datos del sensor ha termiando
    def get_data(self):
        unchanged_count = 0

        # Determinar donde esta el fin de los datos: comprobar que NO hay transicion 0<>1 en 100 ciclos o mas
        max_unchanged_count = 100

        last = -1
        data = []
        while True:
            current = RPi.GPIO.input(self.pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break

        return data

    #Maquina de estados
    def parse_data(self, data):
        STATE_INIT = 1
        STATE_INIT_PULL_UP = 2
        STATE_DATA_FIRST_LOW = 3
        STATE_DATA_HIGH = 4
        STATE_DATA_LOW = 5

        state = STATE_INIT

        lengths = [] # 
        current_length = 0

        for i in range(len(data)):
            current = data[i]
            current_length += 1

            if state == STATE_INIT:
                if current == 0:
                    state = STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_INIT_PULL_UP:
                if current == 1:
                    state = STATE_DATA_FIRST_LOW
                    continue
                else:
                    continue
            if state == STATE_DATA_FIRST_LOW:
                if current == 0:
                    state = STATE_DATA_HIGH
                    continue
                else:
                    continue
            if state == STATE_DATA_HIGH:
                if current == 1:
                    current_length = 0
                    state = STATE_DATA_LOW
                    continue
                else:
                    continue
            if state == STATE_DATA_LOW:
                if current == 0:
                    lengths.append(current_length)
                    state = STATE_DATA_HIGH
                    continue
                else:
                    continue

        return lengths

    def calculate_bits(self, data_lengths):
        # encontrar periodo mas largo y mas corto para establecer umbral entre 0 y 1
        shortest_pull_up = 1000
        longest_pull_up = 0

        for i in range(0, len(data_lengths)):
            length = data_lengths[i]
            if length < shortest_pull_up:
                shortest_pull_up = length
            if length > longest_pull_up:
                longest_pull_up = length
        
        # la mitad del valor lo usamos para distinguir entre 0 y 1
        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []

        for i in range(0, len(data_lengths)):
            bit = 0
            if data_lengths[i] > halfway:
                bit = 1
            bits.append(bit)

        return bits

#Función que limpia la pantalla
def clear_display():
    bus.write_byte_data(i2c_adress,0x80,0x01)

#Función que para la comunicación GPIO
def destroy():
	GPIO.cleanup()
    
#Main de la aplicación
if __name__ == '__main__':# Program start from here
    try:
        moisture = 0
        while moisture < 19:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            # Ejemplo usando del GPIO 5
            instance = DHT11(pin=5)
            #Se inicializa el puerto digital 26 para el buzzer
            buzzer = 26
            GPIO.setup(buzzer, GPIO.OUT)
            humedad_deseada=20
            #Se leen los parametros de humedad y temperatura
            print('Detecting moisture...')
            result_temperature,result_humidity = instance.read()
            moisture = int(result_humidity)
            if moisture > 19:
                #Se almacena la fecha y hora de la medición
                current_time = datetime.datetime.now()
                #Se muestra por pantalla los datos
                text = "Humedad:"+str(moisture)+"% \n"+str(current_time)
                setText(text)
                #Si la humedad deseada sobrepasa un 75% tanto por arriba como por abajo la tomada se activa el buzzer
                if (moisture < int(humedad_deseada * 0.75) or moisture > int(humedad_deseada / 0.75)):
                    for i in range(49):
                        print(i)
                        GPIO.output(buzzer, GPIO.HIGH)
                        time.sleep(1)
                        GPIO.output(buzzer, GPIO.LOW)
                        time.sleep(17)
                time.sleep(10)
            #Se limpia la pantalla
            clear_display()
        #Se puede parar la aplicación con 'Ctrl+C'
    except KeyboardInterrupt:  
        clear_display()
        destroy()


