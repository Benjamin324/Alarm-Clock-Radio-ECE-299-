from machine import Pin
import time

button = machine.Pin(16,Pin.IN,Pin.PULL_DOWN)
while (True):
    print (button.value())
    time.sleep_ms(10)
