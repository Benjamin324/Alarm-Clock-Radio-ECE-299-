        ##### Import Libraries

import machine
from machine import Pin, SPI, I2C
from ssd1306 import SSD1306_SPI
import utime
import time
import framebuf
from lcd_lib import LCD_1inch3 as LCD #Change font

        ##### Initalize Display

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


        ##### Initialize Radio

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

    
fm_radio = Radio( 101.9, 5, False ) #initialize radio module


        ####Continuous Items

        #Convert to Local time(not Implemented)
#machine.RTC().datetime(thistuple)

        #Time Top Right

time_text = str((time.localtime()[3]) )+ ":" + str(time.localtime()[4]) 
print(time_text)
while True:
    oled.fill(0) #clear buffer
   # radio_text = str(fm_radio.GetSettings()[2]) + " fm"
   # oled.fill(0) # clear buffer
    LCD.write_text(time_text,x=0,y=0,size=1,color=1)
    oled.show()
    LCD.show()