        ### Import Libraries

from machine import Pin, SPI, I2C
from ssd1309 import SSD1309_SPI
import framebuf
import time


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
oled = SSD1309_SPI( SCREEN_WIDTH, SCREEN_HEIGHT, oled_spi, spi_dc, spi_res, spi_cs, True )


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

fm_radio = Radio( 101.9, 5, False )


        ### Init Encoder

a = Pin(14, Pin.IN, Pin.PULL_DOWN)
b = Pin(13, Pin.IN, Pin.PULL_DOWN)
button = Pin(15, Pin.IN, Pin.PULL_DOWN)
last_a = a.value()


def debounce():
    global deb_clock
    
    deb_current = time.ticks_ms() # get time of press
    if deb_current > (deb_clock + deb_time): # compare to debounce counter
        deb_clock = deb_current # reset debounce counter
        return True # sucessful click
    else:
        return False # rejected (debounced) click


def encoder_irq(pin):
    global last_a
    current_a = a.value()
    if debounce():
        if current_a != last_a:
                if b.value() != current_a:
                    left_turn()
                else:
                    right_turn()


def button_irq(pin):
    if debounce():
        centre_press()
        

a.irq(trigger=Pin.IRQ_RISING,
      handler=encoder_irq)

button.irq(trigger=Pin.IRQ_RISING,
      handler=button_irq)


        ### Global Vars

mode = 0                       # tracks which screen mode is active (always %4)
menu_sel = 0                   # tracks which menu option is highlighted w/ carrot
set_time = [0,0]               # temp time array for setting alarm/time (elements are always %12)
alarm = [0,0]
set_seg = 0                    # tracks which time segment (H/M) is being set
set_mode = False               # tracks if current set_time is to be written to clock (False) or to alarm (True)
time_format = True
alarm_set = True
deb_time = 40                  # Debounce time in ms
deb_clock = 0                  # Timer for debouncing script


        ### UI Button Funcs

def right_turn():
    global mode, menu_sel, set_time
    
    if mode == 0: # Main
        vol = fm_radio.GetSettings()[1] # fetch current volume
        if vol == 15: # 15 is max volume
            pass
        else:
            vol += 1 # increment volume
            if ( fm_radio.SetVolume( vol ) == True ): # write vol value to module
                fm_radio.ProgramRadio()
            else:
                print( "Invalid volume level" )
            
    
    elif mode == 1: # Settings
        menu_sel += 1 # increment highlighted menu option
        
    elif mode == 2: # Timeset
        set_time[(set_seg)] += 1 # increment the relevant time segment in the temp set_time array
            
    elif mode == 3: # Radioset
        freq = fm_radio.GetSettings()[2] # fetch current tuned frequency
        print(freq)
        if freq == 108.0: # max freq
            pass
        else:
            freq += 0.1 # increment freq
            if ( fm_radio.SetFrequency( freq ) == True ): # write freq to module
                fm_radio.ProgramRadio()
            else:
                print( "Invalid frequency" )
    
    else:
        print("invalid mode in right_turn()") # mode should not be > 3
    
    print("right turn")
    return

def left_turn():
    global mode, menu_sel, set_time
    
    if mode == 0: # Main
        vol = fm_radio.GetSettings()[1]
        if vol == 0:
            pass
        else:
            vol -= 1
            if ( fm_radio.SetVolume( vol ) == True ):
                fm_radio.ProgramRadio()
            else:
                print( "Invalid volume level" )
    
    elif mode == 1: # Settings
        menu_sel -= 1
        
    elif mode == 2: # Timeset
        set_time[(set_seg)] -= 1
        
    elif mode == 3: # Radioset
        freq = fm_radio.GetSettings()[2] # fetch current tuned frequency
        if freq == 88.0: # min freq
            pass
        else:
            freq -= 0.1 # increment freq
            if ( fm_radio.SetFrequency( freq ) == True ): # write freq to module
                fm_radio.ProgramRadio()
            else:
                print( "Invalid frequency" )
    
    else:
        print("invalid mode in left_turn()")
        
    print("left turn")
    return

def centre_press():
    global mode, menu_sel, set_mode, set_seg, set_time, alarm
    
    if mode == 0: # Main
        menu_sel = 0 # reset highlighted menu option
        mode = 1 # enter settings screen mode
        
    elif mode == 1: # Settings
        if (menu_sel % 4) == 0: # 'set clock' has been pressed
            set_time[0] = machine.RTC().datetime()[4] # set temp set_time Hr from current internal clock
            set_time[1] = machine.RTC().datetime()[5] # set temp set_time Min from current internal clock
            set_mode = False # set_mode indicates clock is being set (not alarm)
            set_seg = 0 # reset set_seg
            mode = 2
            
        elif (menu_sel % 4) == 1: # 'set alarm' has been pressed
            set_time[0] = alarm[0] # set temp set_time Hr from alarm Hr
            set_time[1] = alarm[1] # set temp set_time Min from alarm Min
            set_mode = True # set_mode indicates alarm is being set (not clock)
            set_seg = 0 # reset set_seg
            mode = 2
            
        elif (menu_sel % 4) == 2: # 'set radio' is pressed
            mode = 3 # set mode to Radioset
            
        else: # 'Exit' pressed
            mode = 0 # mode back to main screen mode
        
    elif mode == 2: # Timeset
        set_seg += 1 # increment set_seg
        if set_seg > 1: # if all clock segments have been set
            if set_mode == True: # setting alarm
                alarm[0] = set_time[0]
                alarm[1] = set_time[1]
            else: # setting time
                machine.RTC().datetime((machine.RTC().datetime()[0],machine.RTC().datetime()[1],machine.RTC().datetime()[2],machine.RTC().datetime()[3],set_time[0],set_time[1],machine.RTC().datetime()[6],machine.RTC().datetime()[7]))
            set_seg = 0
            mode = 0
                
    elif mode == 3: # Radioset
        mode = 0 # return to main screen mode
        
    else:
        print("invalid mode in centre_press")
        
    print("centre press")
    return


def run_alarm():
    Pin(28, Pin.OUT).value(1)


        ### Screen Draw funcs

def draw_main():
    # draw clock
    print_time = "{:02d}:{:02d}".format((machine.RTC().datetime()[4]),(machine.RTC().datetime()[5]))
    oled.text(print_time,40,30)
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
    print_time = "{:02d}:{:02d}".format((set_time[0]),(set_time[1]))
    oled.text(print_time,40,30)
    return

def draw_radioset():
    # draw set radio
    print_freq = str(fm_radio.GetSettings()[2])
    oled.text(print_freq,40,30)
    return


        ### Alarm func

def alarm_check():
    if alarm_set: # alarm is on
        if alarm[0] == machine.RTC().datetime()[4]:
            if alarm[1] == machine.RTC().datetime()[5]:
                run_alarm()
    return


        ### Main sequence
    
while(True):

    oled.fill(0) # clear buffer
    
    alarm_check()
    
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