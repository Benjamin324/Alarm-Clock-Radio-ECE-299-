from ssd1306 import SSD1306_SPI
from machine import Pin,SPI,PWM
import framebuf
import time
import os

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


class LCD_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 64
        
        #Removed Blue R G  
        self.white =   1
        self.black =   0
         # Add buffer and FrameBuffer init
        self.buffer = bytearray(self.width * self.height * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

        # Add pins (reuse your existing SPI pins)
        self.cs  = Pin(17, Pin.OUT)
        self.dc  = Pin(20, Pin.OUT)
        self.rst = Pin(21, Pin.OUT)
        self.spi = SPI(0, baudrate=100000, sck=Pin(18), mosi=Pin(19))

        self.init_display()
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize dispaly"""  
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A) 
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35) 

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)   

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F) 

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)
        
        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
    def render(self,image_name,offset_x=0,offset_y=0,background=None,show_rendering=True):
        '''Method to render 16-Bit images on the LCD panel

            Args:
                image_name: path of the encoded image
                offset_x: x co-ordinate of starting position
                offset_y: y co-ordinate of starting position
                background: color of the background
                show_rendering: if True, the process of rendering is shown, else a loading screen is shown
        '''
        self.fill(background)

        f = open(image_name,'r')

        row_count = 0

        while True:
            data = f.readline()
            if not data:
                break
            px_ptr = 0
            # All Even Positions will be Pixel Counts and
            # odd positions will be Pixel Color Values
            data = data.split(',')
            for i in range(len(data)):
                # Reading Count of Homogenous Pixels
                if i%2 == 0:
                    px_count = int(data[i])
                # Reading the Color of the Homogenous Pixels
                else:
                    color = int('0x'+data[i])
                    if color != background:
                        self.hline(px_ptr+offset_x,row_count+offset_y,px_count,color)            
                    px_ptr += px_count
                    
            row_count += 1
            if show_rendering:
                self.show()
            
    def write_text(self,text,x,y,size,color):
        ''' Method to write Text on OLED/LCD Displays
            with a variable font size

            Args:
                text: the string of chars to be displayed
                x: x co-ordinate of starting position
                y: y co-ordinate of starting position
                size: font size of text
                color: color of text to be displayed
        '''
        background = self.pixel(x,y)
        info = []
        # Creating reference charaters to read their values
        self.text(text,x,y,color)
        for i in range(x,x+(8*len(text))):
            for j in range(y,y+8):
                # Fetching amd saving details of pixels, such as
                # x co-ordinate, y co-ordinate, and color of the pixel
                px_color = self.pixel(i,j)
                info.append((i,j,px_color)) if px_color == color else None
        # Clearing the reference characters from the screen
        self.text(text,x,y,background)
        # Writing the custom-sized font characters on screen
        for px_info in info:
            self.fill_rect(size*px_info[0] - (size-1)*x , size*px_info[1] - (size-1)*y, size, size, px_info[2]) 
        

