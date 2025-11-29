# app_improved_ui.py
from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# --- Configuration: set these in environment variables or paste directly (not recommended) ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDXmAjVgoQ_bA_vqN7hRynPdltapkBB5Kk")
GOOGLE_CX = os.getenv("GOOGLE_CX", "74c4569930da44bb3")

# --- Simple rule-based answers ---
RULES = {
    "hello": "Hello! Welcome to Strata — your smart assistant. How can I help you today? How can I help you today?",
    "hi": "Hi! Ask me anything or type 'search: your query' to fetch from Google.",
    "who are you": "I'm a simple chatbot that can answer basic questions and search Google for you.",
    "help": "Try: 'What is Python?', or 'search: best coffee near me'."
}

def rule_based_answer(text):
    t = text.strip().lower()
    return RULES.get(t)

# --- Google Custom Search helper ---
def google_search(query, num=3):
    if not GOOGLE_API_KEY or not GOOGLE_CX or "YOUR_GOOGLE_API_KEY" in GOOGLE_API_KEY:
        return {"error": "Google API not configured. Set GOOGLE_API_KEY and GOOGLE_CX."}
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "num": num}
    resp = requests.get(url, params=params, timeout=8)
    if resp.status_code != 200:
        return {"error": f"Search API returned {resp.status_code}: {resp.text}"}
    data = resp.json()
    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet")
        })
    return {"results": results}

# --- Very small summarizer: pick top snippets ---
def summarize_search(results):
    if "error" in results:
        return results["error"]
    items = results.get("results", [])
    if not items:
        return "No good results found on Google."
    # return short combined snippet
    snippets = [it["snippet"] for it in items if it.get("snippet")]
    summary = " ".join(snippets[:2])
    return summary if summary else items[0].get("title", "Found something but couldn't summarize.")

# --- Chat endpoint ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    text = data.get("message", "").strip()
    if not text:
        return jsonify({"reply": "Please send a message."})
    # If user explicitly asks to search: "search: ..."
    if text.lower().startswith("search:"):
        q = text.split(":", 1)[1].strip()
        g = google_search(q)
        if "error" in g:
            return jsonify({"reply": g["error"], "meta": g})
        return jsonify({"reply": summarize_search(g), "meta": g})
    # Rule-based fallback
    rb = rule_based_answer(text)
    if rb:
        return jsonify({"reply": rb})
    # Otherwise call Google automatically (fallback)
    g = google_search(text)
    if "error" in g:
        # fallback to a generic reply
        return jsonify({"reply": "Sorry, I couldn't fetch search results right now. Try again later."})
    return jsonify({"reply": summarize_search(g), "meta": g})

# Improved, modern-looking UI
INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Strata</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg: #0f172a;
      --card: linear-gradient(135deg,#0f172a 0%,#0b1220 100%);
      --accent: #7c3aed;
      --muted: #94a3b8;
      --glass: rgba(255,255,255,0.04);
    }
    *{box-sizing:border-box;font-family:Inter,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial}
    body{margin:0;min-height:100vh;background:linear-gradient(180deg,#071028 0%, #07172a 100%);display:flex;align-items:center;justify-content:center;padding:24px;color:#e6eef8}
    .wrap{width:100%;max-width:920px;background:var(--card);border-radius:14px;box-shadow:0 10px 30px rgba(2,6,23,0.6);overflow:hidden;border:1px solid rgba(255,255,255,0.03);}
    header{display:flex;align-items:center;gap:12px;padding:18px 20px;border-bottom:1px solid rgba(255,255,255,0.03)}
    .brand{display:flex;align-items:center;gap:12px}
    .logo{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#3b82f6);display:flex;align-items:center;justify-content:center;font-weight:700;color:white}
    .title{font-weight:600}
    .subtitle{font-size:12px;color:var(--muted);margin-top:2px}

    .content{display:grid;grid-template-columns:1fr 360px;gap:20px;padding:20px}
    @media (max-width:880px){.content{grid-template-columns:1fr;}.sidebar{order:2}}

    .chat-card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:10px;padding:16px;display:flex;flex-direction:column;height:560px}
    .messages{flex:1;overflow:auto;padding:6px 6px 12px;display:flex;flex-direction:column;gap:10px}

    .msg{max-width:78%;padding:10px 14px;border-radius:12px;line-height:1.35}
    .msg.me{align-self:flex-end;background:linear-gradient(90deg,var(--accent),#4f46e5);color:white;border-bottom-right-radius:4px}
    .msg.bot{align-self:flex-start;background:var(--glass);color:#e6eef8;border-bottom-left-radius:4px}
    .meta{font-size:11px;color:var(--muted);margin-top:6px}

    .input-row{display:flex;gap:10px;padding-top:12px}
    .input-row input{flex:1;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:inherit;font-size:14px}
    .btn{background:linear-gradient(90deg,var(--accent),#4f46e5);border:none;padding:10px 14px;border-radius:10px;color:white;font-weight:600;cursor:pointer}
    .btn:active{transform:translateY(1px)}

    .sidebar{padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);height:560px;display:flex;flex-direction:column;gap:12px}
    .card-title{font-weight:600}
    .hint{font-size:13px;color:var(--muted)}
    .history{flex:1;overflow:auto;padding-top:6px;display:flex;flex-direction:column;gap:8px}
    .history button{background:transparent;border:1px dashed rgba(255,255,255,0.03);padding:10px;border-radius:8px;color:var(--muted);text-align:left;cursor:pointer}
    .footer{padding:12px;border-top:1px solid rgba(255,255,255,0.02);display:flex;justify-content:space-between;align-items:center}

    a.link{color:#93c5fd;text-decoration:none;font-size:13px}
    .typing{height:14px;width:40px;background:linear-gradient(90deg,#fff,#fff);opacity:0.12;border-radius:10px;position:relative}
    .dot{width:6px;height:6px;background:white;border-radius:50%;position:absolute;top:4px;opacity:0.9;animation:blink 1.2s infinite}
    .dot:nth-child(1){left:6px;animation-delay:0s}
    .dot:nth-child(2){left:17px;animation-delay:0.15s}
    .dot:nth-child(3){left:28px;animation-delay:0.3s}
    @keyframes blink{0%{opacity:0.1}50%{opacity:0.9}100%{opacity:0.1}}

  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">
        <div class="logo">C</div>
        <div>
          <div class="title">Strata</div>
          <div class="subtitle">Simple answers + Google search</div>
        </div>
      </div>
    </header>

    <div class="content">
      <div class="chat-card">
        <div id="messages" class="messages" aria-live="polite"></div>

        <div class="input-row">
          <input id="msg" placeholder="Ask something or type 'search: your query'" autocomplete="off" />
          <button class="btn" id="send">Send</button>
        </div>
      </div>

      <aside class="sidebar">
        <div>
          <div class="card-title">Quick tips</div>
          <div class="hint">Use <strong>search: pizza near me</strong> to force web search. Short questions will be answered instantly if they match a rule.</div>
        </div>

        <div>
          <div class="card-title">Recent searches</div>
          <div id="history" class="history"></div>
        </div>

        <div class="footer">
          <div style="font-size:13px;color:var(--muted)">Local demo</div>
          <div style="font-size:13px;color:var(--muted)">v1.0</div>
        </div>
      </aside>
    </div>
  </div>

<script>
const messagesEl = document.getElementById('messages');
const historyEl = document.getElementById('history');
const input = document.getElementById('msg');
const sendBtn = document.getElementById('send');
let history = [];

function escapeHtml(s){
  return s.replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
  });
}

function appendMessage(text, who='bot', meta=null){
  const div = document.createElement('div');
  div.className = 'msg ' + (who==='me' ? 'me' : 'bot');
  // convert URLs to anchors
  const content = escapeHtml(text).replace(/(https?:\/\/[^\s]+)/g, function(url){
    return '<a class="link" href="'+url+'" target="_blank" rel="noopener noreferrer">'+url+'</a>';
  });
  div.innerHTML = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  if(meta && meta.results){
    meta.results.forEach(r=>{
      const linkDiv = document.createElement('div');
      linkDiv.className = 'msg bot';
      linkDiv.style.maxWidth='100%';
      linkDiv.innerHTML = '<strong>'+escapeHtml(r.title||'')+'</strong><div style="font-size:13px;color:var(--muted)">'+escapeHtml(r.snippet||'')+'</div><div style="margin-top:6px"><a class="link" href="'+escapeHtml(r.link||'#')+'" target="_blank" rel="noopener noreferrer">Open source</a></div>';
      messagesEl.appendChild(linkDiv);
    });
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
}

function appendUser(text){
  const div = document.createElement('div');
  div.className = 'msg me';
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setTyping(on){
  if(on){
    const t = document.createElement('div');
    t.className='msg bot';
    t.id='__typing';
    t.innerHTML = '<div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
    messagesEl.appendChild(t);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  } else {
    const t = document.getElementById('__typing');
    if(t) t.remove();
  }
}

async function sendMsg(){
  const text = input.value.trim();
  if(!text) return;
  appendUser(text);
  input.value='';
  addToHistory(text);
  setTyping(true);

  try{
    const res = await fetch('/api/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message: text})
    });
    const j = await res.json();
    setTyping(false);
    appendMessage(j.reply || 'No reply', 'bot', j.meta);
  }catch(e){
    setTyping(false);
    appendMessage('Network error. Could not reach server.', 'bot');
  }
}

function addToHistory(q){
  history.unshift(q);
  if(history.length>8) history.pop();
  renderHistory();
}

function renderHistory(){
  historyEl.innerHTML='';
  history.forEach(h=>{
    const btn = document.createElement('button');
    btn.textContent = h.length>48 ? h.slice(0,46)+'...' : h;
    btn.onclick = ()=>{ input.value = h; input.focus(); };
    historyEl.appendChild(btn);
  });
}

sendBtn.addEventListener('click', sendMsg);
input.addEventListener('keydown', (e)=>{
  if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendMsg(); }
});

// starter message
appendMessage('Hello there! I can answer quick questions or look things up on the web. ');
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
