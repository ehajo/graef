import board
import busio
import wifi
import socketpool
import usb_cdc
import time
from adafruit_httpserver.server import Server
from adafruit_httpserver.response import Response
from secrets import secrets

serial = usb_cdc.console

uart_graef = busio.UART(tx=board.GP0, rx=board.GP1, baudrate=9600)
uart_tastenfeld = busio.UART(tx=board.GP4, rx=board.GP5, baudrate=9600)

serial.write(b"Connecting to WiFi...\n")
wifi.radio.connect(secrets["wifi_ssid"], secrets["wifi_password"])
ip_address = str(wifi.radio.ipv4_address)
serial.write(f"Connected to WiFi. IP: {ip_address}\n".encode('utf-8'))

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

machine_status = "off"
pending_toggle = False
toggle_sent = False
last_sent_status = None

packet_off = b'\xAA\x00\x60\x8A\x9C\xE8\x03\x02\x1D\x55'
packet_starting = b'\xAA\xA0\x60\x8A\x9C\xE8\x03\x02\xBD\x55'
packet_ready = b'\xAA\xC0\x60\x8A\x9C\xE8\x03\x02\xDD\x55'

status_map = {
    "off": "Ausgeschaltet",
    "starting": "Startet...",
    "ready": "Bereit zum Brühen ☕"
}

html_template = """
<!DOCTYPE html>
<html lang=\"de\">
<head>
    <meta charset=\"UTF-8\">
    <title>Pico W Kaffeemaschine</title>
    <style>
        body {{
            background-color: #f5f5f5;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 40px;
        }}
        h1 {{
            color: #333;
        }}
        .button {{
            padding: 15px 30px;
            font-size: 18px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        .button:hover {{
            background-color: #0056b3;
        }}
        .status {{
            margin-top: 30px;
            font-size: 24px;
            color: #444;
        }}
    </style>
</head>
<body>
    <h1>Pico W Kaffeemaschine</h1>
    <form action=\"/button\" method=\"POST\">
        <input class=\"button\" type=\"submit\" value=\"Kaffeemaschine umschalten\">
    </form>
    <div class=\"status\">Status: {status}</div>
</body>
</html>
"""

@server.route("/")
def base(request):
    html = html_template.format(status=status_map.get(machine_status, "Unbekannt"))
    return Response(request, html, content_type="text/html")

@server.route("/button", "POST")
def button(request):
    global pending_toggle
    try:
        pending_toggle = True
        serial.write(b"[HTTP] Button gedrückt, Umschaltung ausstehend\n")
        html = html_template.format(status=status_map.get(machine_status, "Unbekannt"))
        return Response(request, html, content_type="text/html")
    except Exception as e:
        serial.write(f"[ERROR] Button handler exception: {str(e)}\n".encode("utf-8"))
        return Response(request, "Fehler bei der Verarbeitung.", content_type="text/plain")

serial.write(("Starting server at http://" + ip_address + ":80\n").encode('utf-8'))
server.start(host=ip_address, port=80)

buffer_graef = bytearray()
buffer_tastenfeld = bytearray()
last_time_graef = time.monotonic()
last_time_tastenfeld = time.monotonic()
timeout = 0.005
max_buffer_size = 10

while True:
    server.poll()
    current_time = time.monotonic()

    if uart_graef.in_waiting:
        data = uart_graef.read(uart_graef.in_waiting)
        if data:
            buffer_graef.extend(data)
            last_time_graef = current_time
            if len(buffer_graef) >= 10:
                candidate = bytes(buffer_graef[:10])
                if candidate == packet_off:
                    machine_status = "off"
                elif candidate == packet_starting:
                    machine_status = "starting"
                elif candidate == packet_ready:
                    machine_status = "ready"

    if uart_tastenfeld.in_waiting:
        data = uart_tastenfeld.read(uart_tastenfeld.in_waiting)
        if data:
            buffer_tastenfeld.extend(data)
            last_time_tastenfeld = current_time

    if pending_toggle and not toggle_sent:
        buffer_tastenfeld = bytearray()
        buffer_tastenfeld.extend(b'\xAA\x01\x60\x8A\x9C\xE8\x03\x00\x1C\x55')
        # uart_graef.write(alt_sequence)
        serial.write(b"[UART] Umschaltbefehl gesendet\n")
        last_sent_status = machine_status
        toggle_sent = True

    if toggle_sent and machine_status != last_sent_status:
        serial.write(f"[STATE] Statuswechsel: {last_sent_status} -> {machine_status}\n".encode("utf-8"))
        pending_toggle = False
        toggle_sent = False
        last_sent_status = None

    if len(buffer_graef) >= max_buffer_size:
        uart_tastenfeld.write(buffer_graef)
        buffer_graef = bytearray()
    elif buffer_graef and (current_time - last_time_graef >= timeout):
        uart_tastenfeld.write(buffer_graef)
        buffer_graef = bytearray()

    if len(buffer_tastenfeld) >= max_buffer_size:
        uart_graef.write(buffer_tastenfeld)
        buffer_tastenfeld = bytearray()
    elif buffer_tastenfeld and (current_time - last_time_tastenfeld >= timeout):
        uart_graef.write(buffer_tastenfeld)
        buffer_tastenfeld = bytearray()

    time.sleep(0.001)