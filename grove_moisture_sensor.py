#Se importan las librerías necesarias
import math
import sys
import time
#Se utiliza el archivo adc proporcionado por la librería grove
from adc import ADC

__all__ = ["GroveMoistureSensor"]
#Se define la clase GroveMoisture
class GroveMoistureSensor:
    '''
    Grove Moisture Sensor class

    Args:
        pin(int): number of analog pin/channel the sensor connected.
    '''
    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC()

    @property
    def moisture(self):
        '''
        Get the moisture strength value/voltage

        Returns:
            (int): voltage, in mV
        '''
        value = self.adc.read_voltage(self.channel)
        return value

Grove = GroveMoistureSensor

