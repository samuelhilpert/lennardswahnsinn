from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from datetime import datetime

app = FastAPI()

# ===== Zustand (ersetzt Arduino-Variablen) =====
STATE = {
    "fill_level": 0,
    "distance": None,
    "lid_open": False,
    "last_update": None,
}

# ===== Datenmodell vom Arduino =====
class UpdatePayload(BaseModel):
    fill_level: int
    distance: float | None = None
    lid_open: bool

# ===== Arduino -> Backend =====
@app.post("/api/update_status")
def update(payload: UpdatePayload):
    STATE["fill_level"] = payload.fill_level
    STATE["distance"] = payload.distance
    STATE["lid_open"] = payload.lid_open
    STATE["last_update"] = datetime.utcnow()
    return {"status": "ok"}

@app.get("/api/lid_command")
def lid_command():
    cmd = STATE["command"]
    STATE["command"] = None
    return {"command": cmd}

@app.post("/api/lid_open")
def lid_open():
    STATE["command"] = "open"
    return {"status": "ok"}

@app.post("/api/lid_close")
def lid_close():
    STATE["command"] = "close"
    return {"status": "ok"}

# ===== Hilfsfunktionen (1:1 aus Arduino übernommen) =====
def fill_color_label(pct: int) -> str:
    if pct < 50:
        return "Grün (0–49%)"
    elif pct < 80:
        return "Gelb (50–79%)"
    else:
        return "Rot (ab 80%)"

def render_page():
    pct = STATE["fill_level"]
    dist = STATE["distance"]
    lid_open = STATE["lid_open"]

    if pct < 50:
        bar_color = "#2ecc71"
    elif pct < 80:
        bar_color = "#f1c40f"
    else:
        bar_color = "#e74c3c"

    lid_text = "OFFEN" if lid_open else "GESCHLOSSEN"
    lid_color = "#27ae60" if lid_open else "#7f8c8d"
    dist_text = "--" if dist is None else f"{dist}"

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart-Mülleimer</title>
<style>
body {{
  font-family: Arial, Helvetica, sans-serif;
  background: #f4f6f8;
  margin: 0;
  padding: 0;
}}
.container {{
  max-width: 460px;
  margin: auto;
  padding: 18px;
}}
h1 {{
  text-align: center;
  margin: 10px 0 18px 0;
}}
.card {{
  background: #fff;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  margin-bottom: 14px;
}}
.row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.big {{
  font-size: 1.3em;
  font-weight: bold;
}}
.badge {{
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: bold;
  color: white;
  background: {lid_color};
}}
.bar {{
  width: 100%;
  height: 24px;
  background: #e6e6e6;
  border-radius: 999px;
  overflow: hidden;
  margin-top: 10px;
}}
.fill {{
  height: 100%;
  width: {pct}%;
  background: {bar_color};
  transition: width 0.5s;
}}
.small {{
  color: #666;
  font-size: 0.95em;
}}
.footer {{
  text-align: center;
  color: #888;
  font-size: 0.9em;
  margin-top: 6px;
}}
</style>
</head>
<body>
  <div class="container">
    <h1>Smart-Mülleimer</h1>

    <div class="card">
      <div class="row">
        <div class="big">Deckel</div>
        <div class="badge">{lid_text}</div>
      </div>
      <div style="margin-top:10px;">
            <button class="button" onclick="sendCommand('open')">Deckel öffnen</button>
            <button class="button" onclick="sendCommand('close')">Deckel schließen</button>
        </div>
    </div>

    <div class="card">
      <div class="row">
        <div class="big">Füllstand</div>
        <div class="big">{pct}%</div>
      </div>
      <div class="bar"><div class="fill"></div></div>
      <div class="small">{fill_color_label(pct)}</div>
    </div>

    <div class="card">
      <div class="row">
        <div class="big">Abstand</div>
        <div class="big">{dist_text} cm</div>
      </div>
      <div class="footer">
        Letztes Update: {STATE["last_update"]}
      </div>
      <button class="button" onclick="location.reload();">Aktualisieren</button>
      

    </div>
  </div>
  
  <script>
async function sendCommand(action) {{
    try {{
        const response = await fetch('/api/lid_' + action, {{ method: 'POST' }});
        if (!response.ok) throw new Error('Fehler');
        console.log('Befehl gesendet:', action);
    }} catch(e) {{
        console.error(e);
    }}
}}
</script>
</body>
</html>
"""

# ===== Browser -> HTML =====
@app.get("/", response_class=HTMLResponse)
def index():
    return render_page()
