
import network
import socket
from machine import Pin, ADC
from time import sleep
from lcd import LCD

# LCD Pins (4-bit mode)
lcd_rs = Pin(0, Pin.OUT)
lcd_en = Pin(1, Pin.OUT)
lcd_d4 = Pin(2, Pin.OUT)
lcd_d5 = Pin(3, Pin.OUT)
lcd_d6 = Pin(4, Pin.OUT)
lcd_d7 = Pin(5, Pin.OUT)

# Initialize LCD
lcd = LCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7)
lcd.clear()

# Potentiometer for contrast (not used in code but wired to LCD VO pin)
potentiometer = ADC(26)

# WiFi credentials
SSID = "hastins"
PASSWORD = "876543210"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print('waiting for connection...')
        sleep(1)
    
    if not wlan.isconnected():
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])
        return status[0]

def web_page(lcd_line1, lcd_line2):
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Pico W LCD Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0 auto;
            padding: 20px;
            max-width: 600px;
            text-align: center;
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        textarea {
            width: 100%;
            height: 80px;
            padding: 10px;
            box-sizing: border-box;
        }
        button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>Pico W LCD Control</h1>
    <form action="/" method="get">
        <div class="container">
            <textarea name="line1" placeholder="Line 1">""" + lcd_line1 + """</textarea>
            <textarea name="line2" placeholder="Line 2">""" + lcd_line2 + """</textarea>
            <button type="submit">Update LCD</button>
        </div>
    </form>
    <div class="status">
        <p>Current LCD Content:</p>
        <p><strong>Line 1:</strong> """ + lcd_line1 + """</p>
        <p><strong>Line 2:</strong> """ + lcd_line2 + """</p>
    </div>
</body>
</html>"""
    return html

def serve(ip):
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)

    lcd_line1 = "Pico W LCD"
    lcd_line2 = "Web Control"
    lcd.clear()
    lcd.write(lcd_line1)
    lcd.set_cursor(0, 1)
    lcd.write(lcd_line2)

    while True:
        try:
            conn, addr = s.accept()
            print('Got a connection from', addr)
            
            request = conn.recv(1024)
            request = str(request)
            print('Request:', request)
            
            # Parse GET parameters
            line1_start = request.find('line1=') + 6
            line1_end = request.find('&line2=')
            if line1_start != 5 and line1_end != -1:
                lcd_line1 = request[line1_start:line1_end]
                lcd_line1 = lcd_line1.replace('+', ' ')
                lcd_line1 = lcd_line1[:16]  # Limit to 16 characters
                
                line2_start = line1_end + 7
                line2_end = request.find(' HTTP/1.1')
                lcd_line2 = request[line2_start:line2_end]
                lcd_line2 = lcd_line2.replace('+', ' ')
                lcd_line2 = lcd_line2[:16]  # Limit to 16 characters
                
                # Update LCD
                lcd.clear()
                lcd.write(lcd_line1)
                lcd.set_cursor(0, 1)
                lcd.write(lcd_line2)
            
            response = web_page(lcd_line1, lcd_line2)
            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send(response)
            conn.close()
            
        except Exception as e:
            print('Error:', e)
            conn.close()

try:
    ip = connect_wifi()
    serve(ip)
except KeyboardInterrupt:
    lcd.clear()
    lcd.write("Goodbye!")
    sleep(2)
    lcd.clear()
except Exception as e:
    lcd.clear()
    lcd.write("Error occurred")
    lcd.set_cursor(0, 1)
    lcd.write(str(e)[:16])
    sleep(5)
    lcd.clear()

