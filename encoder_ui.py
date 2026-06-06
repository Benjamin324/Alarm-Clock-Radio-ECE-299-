        ### Import Libraries

from machine import Pin, SPI, I2C
from ssd1306 import SSD1306_SPI
import framebuf
import time


        ### Global Vars
mode = 0
time_format = True
alarm_set = False
menu_sel = 0
RTC = machine.RTC().datetime()
set_mode = False
alarm = [0,0]
set_time = [0,0]
set_point = 0


        ### Init Screen

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
spi_sck = Pin(18)
spi_sda = Pin(19)
spi_res = Pin(21)
spi_dc  = Pin(20)
spi_cs  = Pin(17) 
SPI_DEVICE = 0
oled_spi = SPI( SPI_DEVICE, baudrate= 100000, sck= spi_sck, mosi= spi_sda )
oled = SSD1306_SPI( SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True )


        ### Init Radio

class Radio:
    def __init__( self, NewFrequency, NewVolume, NewMute ):
        self.Volume = 2
        self.Frequency = 88
        self.Mute = False
        self.SetVolume( NewVolume )
        self.SetFrequency( NewFrequency )
        self.SetMute( NewMute )
        self.i2c_sda = Pin(26)
        self.i2c_scl = Pin(27)
        self.i2c_device = 1 
        self.i2c_device_address = 0x10
        self.Settings = bytearray( 8 )
        self.radio_i2c = I2C( self.i2c_device, scl=self.i2c_scl, sda=self.i2c_sda, freq=200000)
        self.ProgramRadio()

    def SetVolume( self, NewVolume ):
        try:
            NewVolume = int( NewVolume )
        except:
            return( False )
        if ( not isinstance( NewVolume, int )):
            return( False )
        if (( NewVolume < 0 ) or ( NewVolume >= 16 )):
            return( False )
        self.Volume = NewVolume
        return( True )

    def SetFrequency( self, NewFrequency ):
        try:
            NewFrequency = float( NewFrequency )
        except:
            return( False )
        if ( not ( isinstance( NewFrequency, float ))):
            return( False )
        if (( NewFrequency < 88.0 ) or ( NewFrequency > 108.0 )):
            return( False )
        self.Frequency = NewFrequency
        return( True )
        
    def SetMute( self, NewMute ):
        try:
            self.Mute = bool( int( NewMute ))
        except:
            return( False )
        return( True )
    
    def ComputeChannelSetting( self, Frequency ):
        Frequency = int( Frequency * 10 ) - 870
        ByteCode = bytearray( 2 )
        ByteCode[0] = ( Frequency >> 2 ) & 0xFF
        ByteCode[1] = (( Frequency & 0x03 ) << 6 ) & 0xC0
        return( ByteCode )
    
    def UpdateSettings( self ):
        self.Settings = bytearray( 8 )
        if ( self.Mute ):
            self.Settings[0] = 0x80
        else:
            self.Settings[0] = 0xC0
        self.Settings[1] = 0x09 | 0x04
        self.Settings[2:3] = self.ComputeChannelSetting( self.Frequency )
        self.Settings[3] = self.Settings[3] | 0x10
        self.Settings[4] = 0x04
        self.Settings[5] = 0x00
        self.Settings[6] = 0x84
        self.Settings[7] = 0x80 + self.Volume
        self.Settings = self.Settings[:8]

    def ProgramRadio( self ):
        self.UpdateSettings()
        self.radio_i2c.writeto( self.i2c_device_address, self.Settings )
        
    def GetSettings( self ):
        self.RadioStatus = self.radio_i2c.readfrom( self.i2c_device_address, 256 )
        if (( self.RadioStatus[0xF0] & 0x40 ) != 0x00 ):
            MuteStatus = False
        else:
            MuteStatus = True
        VolumeStatus = self.RadioStatus[0xF7] & 0x0F
        FrequencyStatus = (( self.RadioStatus[0x00] & 0x03 ) << 8 ) | ( self.RadioStatus[0x01] & 0xFF )
        FrequencyStatus = ( FrequencyStatus * 0.1 ) + 87.0
        if (( self.RadioStatus[0x00] & 0x04 ) != 0x00 ):
            StereoStatus = True
        else:
            StereoStatus = False
        return( MuteStatus, VolumeStatus, FrequencyStatus, StereoStatus )

fm_radio = Radio( 101.9, 15, False )


        ### Init Encoder

a = Pin(1, Pin.IN, Pin.PULL_UP)
b = Pin(2, Pin.IN, Pin.PULL_UP)
button = Pin(16, Pin.IN, Pin.PULL_DOWN)
last_a = a.value()

def encoder_irq(pin):
    global last_a, mode, menu_sel
    current_a = a.value()
    
    if mode == 0: # main
        if current_a != last_a:
            if b.value() != current_a:
                vol_up()
            else:
                vol_down()
    
    elif mode == 1: # menu
        if current_a != last_a:
            if b.value() != current_a:
                menu_sel += 1
            else:
                menu_sel -= 1
    
    elif mode == 2: # timeset
        if current_a != last_a:
            if b.value() != current_a:
                if set_point == 0:
                    set_time[0] += 1
                else:
                    set_time[1] += 1
            else:
                if set_point == 0:
                    set_time[0] -= 1
                else:
                    set_time[1] -= 1
    
    elif mode == 3: # radioset
        if current_a != last_a:
            if b.value() != current_a:
                #cw
                pass
            else:
                #ccw
                pass
    
    else: # invalid mode
        print("invalid mode in rotary IRQ")

    last_a = current_a

def button_irq(pin):
    global mode, set_time, set_point, set_mode
    if mode == 0:
        # main clock
        mode = 1 # enter menu
        
    elif mode == 1:
        # menu screen
        if (menu_sel % 4) == 0: #set time
            mode = 2
            set_time[0] = RTC[4]
            set_time[1] = RTC[5]
            set_mode = False
        elif (menu_sel % 4) == 1: #set alarm
            mode = 2
            set_point = 0
            set_time[0] = alarm[0]
            set_time[1] = alarm[1]
            set_mode = True
        elif (menu_sel % 4) == 2: #set radio
            mode = 3
        elif (menu_sel % 4) == 3: #exit
            mode = 0
            mode_sel = 0
            
    elif mode == 2:
        # timeset
        if set_point == 0:
            set_point = 1
        elif set_point == 1:
            if set_mode:
                alarm = set_time
            else:
                machine.RTC().datetime((RTC[0],RTC[1],RTC[2],RTC[3],set_time[0],set_time[1],RTC[6],RTC[7]))
            mode = 0
    
    elif mode == 3:
        #radioset
        pass
    else:
        print("invalid mode in button irq")

a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
      handler=encoder_irq)

button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
      handler=button_irq)


        ### Drawing sequences

def draw_main():
    # draw clock
    print_time = str(RTC[4]) + ":" + str(RTC[5])
    oled.text(print_time,0,0)
    return

def draw_menu():
    # draw menu
    oled.text("Set time",10,0)
    oled.text("Set alarm",10,10)
    oled.text("Tune radio",10,20)
    oled.text("Exit",10,30)
    # draw carrot
    oled.text(">",0,((menu_sel % 4) * 10))
    return

def draw_timeset():
    # draw set time screen
    print_time = str(set_time[0]) + ":" + str(set_time[1])
    oled.text(print_time,0,0)
    return

def draw_radioset():
    # draw set radio
    return


        ### Main sequence
    
while(True):

    oled.fill(0) # clear buffer
    
# Draw screen for current mode    
    if mode == 0: # main
        draw_main()
    elif mode == 1: # menu
        draw_menu()
    elif mode == 2: # timeset
        draw_timeset()
    elif mode == 3: # radio set
        draw_radioset()
    else:
        print("invalid mode in screen draw")

# Push screen to buffer
    oled.show()
        