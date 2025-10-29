import socket, json
import RPi.GPIO as GPIO

# GPIO / PWM
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

PINS = [12, 13, 18]
FREQ = 500
levels = [0, 0, 0]      # duty cycles
pwms = []
for pin in PINS:
    GPIO.setup(pin, GPIO.OUT)
    p = GPIO.PWM(pin, FREQ)
    p.start(0)
    pwms.append(p)

def set_level(i, v):
    v = max(0, min(100, int(v)))
    levels[i] = v
    pwms[i].ChangeDutyCycle(v)

def recv_request(conn):
    """Read up to a few KB and return decoded text."""
    return conn.recv(8192).decode("utf-8", errors="ignore")

def parse_request_line(req_text):
    first = req_text.split("\r\n", 1)[0]
    parts = first.split()
    if len(parts) >= 2:
        return parts[0], parts[1]   # method, path
    return "GET", "/"

def parse_post_body(req_text):
    i = req_text.find("\r\n\r\n")
    if i < 0: return {}
    body = req_text[i+4:]
    out = {}
    for pair in body.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            out[k] = v
    return out

def send_html(conn, html):
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
    conn.sendall(html.encode("utf-8"))

def send_json(conn, obj):
    data = json.dumps(obj)
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
    conn.sendall(data.encode("utf-8"))

# HTML + JS (single page)
def page_html():
    # initial values injected from server so labels match immediately
    l0, l1, l2 = levels
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>ENME441 Lab 7 – Problem 2</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 520px; margin: 2rem; }}
    .row {{ display:flex; align-items:center; gap:12px; margin: 12px 0; }}
    .name {{ width: 3.5rem; }}
    .val  {{ width: 3rem; text-align:right; }}
    input[type=range] {{ width: 280px; }}
  </style>
</head>
<body>
  <h3>LED Brightness (live)</h3>

  <div class="row">
    <div class="name">LED1</div>
    <input id="s0" type="range" min="0" max="100" value="{l0}">
    <div class="val"><span id="v0">{l0}</span>%</div>
  </div>

  <div class="row">
    <div class="name">LED2</div>
    <input id="s1" type="range" min="0" max="100" value="{l1}">
    <div class="val"><span id="v1">{l1}</span>%</div>
  </div>

  <div class="row">
    <div class="name">LED3</div>
    <input id="s2" type="range" min="0" max="100" value="{l2}">
    <div class="val"><span id="v2">{l2}</span>%</div>
  </div>

  <script>
    // helper to POST to /set and update labels without reloading
    async function sendLevel(led, level) {{
      try {{
        const body = "led=" + led + "&level=" + level;
        const res = await fetch("/set", {{
          method: "POST",
          headers: {{ "Content-Type": "application/x-www-form-urlencoded" }},
          body
        }});
        const data = await res.json();   // {{ levels: [..,..,..] }}
        document.getElementById("v0").textContent = data.levels[0];
        document.getElementById("v1").textContent = data.levels[1];
        document.getElementById("v2").textContent = data.levels[2];
      }} catch (e) {{
        // ignore network errors for lab simplicity
      }}
    }}

    // attach input handlers (fires while dragging)
    for (let i = 0; i < 3; i++) {{
      const slider = document.getElementById("s" + i);
      slider.addEventListener("input", (e) => {{
        const val = e.target.value;
        document.getElementById("v"+i).textContent = val; // local echo
        sendLevel(i, val);  // POST on every change
      }});
    }}
  </script>
</body>
</html>"""

# server loop
def run(host="", port=8080):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    print(f"Serving http://{host or 'raspberrypi.local'}:{port}")

    try:
        while True:
            conn, addr = s.accept()
            try:
                req = recv_request(conn)
                method, path = parse_request_line(req)

                if method == "GET":            # serve the app
                    send_html(conn, page_html())

                elif method == "POST" and path == "/set":
                    data = parse_post_body(req)
                    if "led" in data and "level" in data:
                        try:
                            i = int(data["led"])
                            if 0 <= i <= 2:
                                set_level(i, int(data["level"]))
                        except ValueError:
                            pass
                    # return JSON so JS can update labels
                    send_json(conn, {"levels": levels})

                else:
                    # minimal 404
                    conn.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")

            finally:
                conn.close()
    finally:
        s.close()

# entry
if __name__ == "__main__":
    try:
        run("", 8080)
    except KeyboardInterrupt:
        print("\nExiting. Cleaning up GPIO...")
    finally:
        for p in pwms: p.stop()
        GPIO.cleanup()
