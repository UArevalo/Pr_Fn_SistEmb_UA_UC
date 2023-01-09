#Author Unai Arevalo & Unai Chasco
#Curso 2022/2023 Sistemas Embebidos. Universidad de Deusto
# ------------------------------------------------


#Se importan las librerías necesarias 
import RPi
import RPi.GPIO as GPIO
import smbus
import time
import datetime
#Se importa la función que mide la humedad del fichero grove_moisture_sensor
from grove_moisture_sensor import GroveMoistureSensor

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

#Función que limpia la pantalla
def clear_display():
    bus.write_byte_data(i2c_adress,0x80,0x01)

#Función que para la comunicación GPIO
def destroy():
	GPIO.cleanup()
    
#Main de la aplicación
if __name__ == '__main__':# Program start from here
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        #Se inicializa el puerto digital 26 para el buzzer
        buzzer = 26
        GPIO.setup(buzzer, GPIO.OUT)
        #Se inicializa el puerto analógico A2 para el sensor de humedad
        PIN = 2
        humedad_deseada=20
        
        print('Detecting moisture...')
        #Se llama a la función que mide la humedad y se transforma
        sensor = GroveMoistureSensor(PIN)
        m = sensor.moisture
        moisture = int(m/7)
        #Se almacena la fecha y hora de la medición
        current_time = datetime.datetime.now()
        #Se muestra por pantalla los datos
        text = "Humedad:"+str(moisture)+"%\n"+str(current_time)
        setText(text)
        #Si la humedad deseada sobrepasa un 75% tanto por arriba como por abajo la tomada se activa el buzzer
        if (moisture < int(humedad_deseada*0.75) | moisture > int(humedad_deseada/0.75)):
            for i in range(49):
                print(i)
                GPIO.output(buzzer, GPIO.HIGH)
                time.sleep(1)
                GPIO.output(buzzer, GPIO.LOW)
                time.sleep(17)
        time.sleep(100)
        #Se limpia la pantalla
        clear_display()
    #Se puede parar la aplicación con 'Ctrl+C'
    except KeyboardInterrupt:  
        clear_display()
        destroy()
