import pigpio
import time

# Define some device constants
LCD_CHR = True
LCD_CMD = False

# Line numbers
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line
LCD_LINES = (LCD_LINE_1, LCD_LINE_2, LCD_LINE_3, LCD_LINE_4)

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

class PIGPIO_LCD(object):

    def __init__(self, pi, rs, en, d4, d5, d6, d7,
                 rows=4, cols=20, backlight=None):
        self.pi = pi
        self.pins = (rs, en, d4, d5, d6, d7)
        self.rs = rs
        self.en = en
        self.d4 = d4
        self.d5 = d5
        self.d6 = d6
        self.d7 = d7
        self.data_pins = (d4, d5, d6, d7)
        self.backlight = backlight
        self.rows = rows
        self.cols = cols

    def _setup(self):
        """Sets up the GPIO pins."""
        for pin in self.pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)

        if self.backlight:
            self.pi.set_mode(self.backlight, pigpio.OUTPUT)

    def lcd_init(self):
        """Initialisation of the display."""
        self.lcd_byte(0x33,LCD_CMD) # 110011 Initialise
        self.lcd_byte(0x32,LCD_CMD) # 110010 Initialise
        self.lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
        self.lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01,LCD_CMD) # 000001 Clear display
        time.sleep(E_DELAY)

    def lcd_byte(self, bits, mode):
        """Send byte to data pins
            bits = data
            mode = True  for character
                   False for command
        """
        self.pi.write(self.rs, int(mode)) # RS

        # High bits
        for pin in self.data_pins:
            self.pi.write(pin, 0)

        if bits&0x10==0x10:
            self.pi.write(self.d4, 1)
        if bits&0x20==0x20:
            self.pi.write(self.d5, 1)
        if bits&0x40==0x40:
            self.pi.write(self.d6, 1)
        if bits&0x80==0x80:
            self.pi.write(self.d7, 1)

        # Toggle 'Enable' pin
        self.lcd_toggle_enable()

        # Low bits
        for pin in self.data_pins:
            self.pi.write(pin, 0)

        if bits&0x01==0x01:
            self.pi.write(self.d4, 1)
        if bits&0x02==0x02:
            self.pi.write(self.d5, 1)
        if bits&0x04==0x04:
            self.pi.write(self.d6, 1)
        if bits&0x08==0x08:
            self.pi.write(self.d7, 1)

        # Toggle 'Enable' pin
        self.lcd_toggle_enable()

    def lcd_toggle_enable(self):
      """Toggle enable pin."""
      time.sleep(E_DELAY)
      self.pi.write(self.en, 1)
      time.sleep(E_PULSE)
      self.pi.write(self.en, 0)
      time.sleep(E_DELAY)

    def lcd_string(self, message, line):
        """Write a message to the display. All formatting should be done prior
           to calling this method.
        """

        # Break if we get an invalid row number
        if line < 0 or line > self.rows:
            return

        # Turn human row index into zero-index
        line_byte = LCD_LINES[line - 1]

        # Put the cursor to the start of the row
        self.lcd_byte(line_byte, LCD_CMD)

        # Write the message
        for i in message:
            self.lcd_byte(ord(i),LCD_CHR)

    def set_backlight(self, flag):
        """Toggle backlight on-off-on."""
        state = 1 if flag else 0
        self.pi.write(self.backlight, state)

    def clear(self):
        """Clears the LCD screen."""
        self.lcd_byte(0x01,LCD_CMD)

    def start(self):
        """Start the LCD screen. Initialise, LED on, clear display."""
        self._setup()
        self.set_backlight(True)
        self.lcd_init()
        self.clear()
