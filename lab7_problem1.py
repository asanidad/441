import socket, RPi.GPIO as GPIO

# GPIO/PWM
GPIO.setwarnings(False); GPIO.setmode(GPIO.BCM)
PINS = [12, 13, 18]
FREQ = 500
levels = [0, 0, 0]
pwms = []
for pin in PINS:
    GPIO.setup(pin, GPIO.OUT)
    p = GPIO.PWM(pin, FREQ); p.start(0); pwms.append(p)

def set_level(i, v):
    v = max(0, min(100, int(v))); levels[i] = v; pwms[i].ChangeDutyCycle(v)

def parse_post(req_text):
    i = req_text.find('\r\n\r\n')
    if i < 0: return {}
    body = req_text[i+4:]
    d = {}
    for kv in body.split('&'):
        if '=' in kv:
            k, v = kv.split('=', 1)
            d[k] = v
    return d

# HTML layout
def page():
    return f"""<!DOCTYPE html>
<html>
<head>
<title>Lab 7 – P1</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    margin: 40px;
  }}
  .box {{
    border: 1px solid #999;
    width: 220px;
    padding: 10px;
  }}
  h3 {{
    margin-top: 0;
  }}
  input[type=range] {{
    width: 100%;
  }}
  ul {{
    padding-left: 15px;
  }}
</style>
</head>
<body>
  <div class="box">
    <h3>Brightness level:</h3>
    <form method="POST" action="/">
      <input type="range" name="level" min="0" max="100" value="0"><br><br>

      <b>Select LED:</b><br>
      <label><input type="radio" name="led" value="0" checked> LED 1 ({levels[0]}%)</label><br>
      <label><input type="radio" name="led" value="1"> LED 2 ({levels[1]}%)</label><br>
      <label><input type="radio" name="led" value="2"> LED 3 ({levels[2]}%)</label><br><br>

      <input type="submit" value="Change Brightness">
    </form>
  </div>
</body>
</html>"""

# HTTP responder
def send_ok(conn, body):
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
    conn.sendall(body.encode())

# server loop
def run(host="", port=8080):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port)); s.listen(3)
    print(f"Serving http://{host or 'raspberrypi.local'}:{port}")
    try:
        while True:
            conn, _ = s.accept()
            try:
                req = conn.recv(4096).decode("utf-8", "ignore")
                if req.startswith("POST"):
                    data = parse_post(req)
                    if "led" in data and "level" in data:
                        try:
                            i = int(data["led"])
                            if 0 <= i <= 2: set_level(i, data["level"])
                        except: pass
                send_ok(conn, page())
            finally:
                conn.close()
    finally:
        s.close()

if __name__ == "__main__":
    try:
        run("", 8080)
    except KeyboardInterrupt:
        pass
    finally:
        for p in pwms: p.stop()
        GPIO.cleanup()