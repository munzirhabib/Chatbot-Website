"""
Lumen - AI chatbot website (single file)
Language : Python (backend), HTML/CSS/JavaScript (frontend)
Framework: Flask (serves the page and the /api/chat endpoint)
3D       : Three.js (42,000 GPU particles that morph as you scroll), smooth scroll: Lenis
AI       : Anthropic Claude API, called from the SERVER so the API key stays secret.
           Set ANTHROPIC_API_KEY in Vercel > Settings > Environment Variables.
           Without a key the chatbot runs in demo mode with ready-made replies.
"""
import os
import re
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, Response

app = Flask(__name__, static_folder=None)

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

SYSTEM_PROMPT = (
    "You are Lumen, a friendly and sharp AI assistant on the Lumen website. "
    "Reply in the same language the user writes in. Keep answers short (under 120 words) "
    "unless the user asks for detail. Use plain text; you may use **bold** and `code`. "
    "Be warm, clear and honest. If you do not know something, say so."
)

# ---------------- CHAT API ----------------
DEMO_REPLIES = [
    (("hello", "hi", "hey", "salam", "assalam"), "Hello! I'm **Lumen**. Ask me anything, from quick explanations to business ideas."),
    (("what can you do", "help", "features", "can you"), "I can **explain** topics, **summarise** text, **translate**, brainstorm ideas, and help with writing or code. Just ask."),
    (("ai", "artificial", "explain"), "AI is software that learns patterns from huge amounts of data, so it can answer questions, write text and recognise images, a bit like a very fast student who has read a lot."),
    (("idea", "business", "startup"), "Here is one: a **local-language AI assistant for small shops**, taking orders on WhatsApp and answering customer questions 24/7."),
    (("price", "cost", "free"), "You can try Lumen for free right here. No account needed."),
    (("who", "name"), "I'm Lumen, an AI assistant with a living 3D core. Nice to meet you!"),
]


def demo_reply(text):
    t = text.lower()
    words = set(re.findall(r"[a-z']+", t))
    for keys, reply in DEMO_REPLIES:
        # single words must match whole words; phrases match anywhere
        if any((k in t) if " " in k else (k in words) for k in keys):
            return reply
    return ("Great question! I'm running in **demo mode** right now, so my answers are limited. "
            "Connect an API key on the server and I can answer anything.")


def clean_messages(raw):
    """Keep only valid user/assistant messages, trimmed, and starting with a user message."""
    out = []
    for m in (raw or [])[-12:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            text = m["content"].strip()[:800]
            if text:
                out.append({"role": m["role"], "content": text})
    while out and out[0]["role"] != "user":
        out.pop(0)
    return out


def call_claude(messages, key):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 400,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = clean_messages(data.get("messages"))
    if not messages:
        return jsonify(reply="Please type a message first."), 400

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:                                   # no key -> demo mode
        return jsonify(reply=demo_reply(messages[-1]["content"]), mode="demo")
    try:
        reply = call_claude(messages, key)
        return jsonify(reply=reply or "I have no answer for that, try rephrasing.", mode="live")
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as e:
        app.logger.error("Claude API error: %s", e)
        return jsonify(reply=demo_reply(messages[-1]["content"]), mode="demo")


@app.route("/")
def home():
    return Response(PAGE, mimetype="text/html")


# ---------------- THE WEBSITE (HTML + CSS + JavaScript) ----------------
PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#06070a">
<title>Lumen | Talk to an AI that feels alive</title>
<meta name="description" content="Lumen is an AI assistant with a living 3D interface. Ask anything, in any language.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='15' fill='%2306070a'/%3E%3Ccircle cx='16' cy='16' r='8' fill='%238ea2ff'/%3E%3Ccircle cx='13' cy='13' r='3' fill='%23fff'/%3E%3C/svg%3E">
<script>
document.documentElement.classList.add("js");
setTimeout(function(){ if(!window.__ok) document.documentElement.classList.add("failsafe"); }, 6000);
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<style>
:root{--bg:#06070a;--fg:#f3f4f8;--mut:#8b90a0;--line:rgba(255,255,255,.09);--acc:#8ea2ff;--warm:#ffc7a0;--glass:rgba(255,255,255,.045);--ease:cubic-bezier(.16,1,.3,1)}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--bg);scroll-behavior:smooth;-webkit-text-size-adjust:100%}
html.lenis,html.lenis body{height:auto}
.lenis.lenis-smooth{scroll-behavior:auto!important}
html:not(.ready){overflow:hidden}
body{font-family:Inter,system-ui,sans-serif;color:var(--fg);background:var(--bg);line-height:1.6;overflow-x:clip;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
button,input,textarea{font:inherit;color:inherit}
button{cursor:pointer;background:none;border:0}
:focus-visible{outline:2px solid var(--acc);outline-offset:3px;border-radius:10px}
::selection{background:var(--acc);color:#06070a}
.d{font-family:"Inter Tight",Inter,sans-serif;font-weight:600;letter-spacing:-.04em;line-height:.95}
.ser{font-family:"Instrument Serif",Georgia,serif;font-style:italic;font-weight:400;letter-spacing:-.01em}
.gt,.gt .wd>span{background:linear-gradient(100deg,var(--acc),var(--warm));-webkit-background-clip:text;background-clip:text;color:transparent}
.i{width:1.2em;height:1.2em;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.skip{position:fixed;left:12px;top:-60px;z-index:400;background:#fff;color:#000;padding:10px 16px;border-radius:10px;font-weight:600;transition:top .2s}
.skip:focus{top:12px}
.lab{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--mut);font-weight:500}
.eyebrow{display:inline-flex;align-items:center;gap:10px;margin-bottom:22px}
.eyebrow::before{content:"";width:28px;height:1px;background:var(--acc)}

/* layers */
.aurora{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(55vw 45vh at 50% 42%,rgba(142,162,255,.13),transparent 70%),radial-gradient(40vw 40vh at 90% 100%,rgba(255,199,160,.07),transparent 70%)}
#gl{position:fixed;inset:0;width:100%;height:100%;z-index:1;pointer-events:none}
.fallback{display:none;position:fixed;left:50%;top:46%;width:min(70vw,560px);aspect-ratio:1;transform:translate(-50%,-50%);border-radius:50%;z-index:1;background:radial-gradient(circle at 40% 35%,rgba(142,162,255,.55),rgba(255,199,160,.18) 55%,transparent 70%);filter:blur(24px)}
.no-gl .fallback{display:block}
main,footer{position:relative;z-index:3}
.wrap{width:min(1240px,90vw);margin:auto}
.sec{position:relative;padding:clamp(90px,15vh,180px) 0}
.veil{background:linear-gradient(180deg,transparent,rgba(6,7,10,.86) 16%,rgba(6,7,10,.86) 84%,transparent)}
h2.d{font-size:clamp(2.4rem,6vw,5.2rem);max-width:15ch}
.lead{color:var(--mut);font-size:clamp(1.02rem,1.5vw,1.25rem);max-width:50ch}

/* word + block reveal */
.wd{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.14em;margin-bottom:-.14em}
.wd>span{display:inline-block}
.js [data-split] .wd>span{transform:translateY(118%);transition:transform 1.15s var(--ease);transition-delay:calc(var(--i)*55ms + var(--d,0ms))}
.js [data-split].in .wd>span,.ready .hero [data-split] .wd>span{transform:none}
.js .rv{opacity:0;transform:translateY(46px);transition:opacity .9s ease,transform 1.2s var(--ease);transition-delay:var(--d,0s)}
.js .rv.in{opacity:1;transform:none}
.js .rvh{opacity:0;transform:translateY(26px);transition:opacity 1s ease,transform 1.2s var(--ease);transition-delay:calc(.75s + var(--k,0)*.1s)}
.ready .rvh{opacity:1;transform:none}
.failsafe .rv,.failsafe .rvh{opacity:1!important;transform:none!important}
.failsafe [data-split] .wd>span{transform:none!important}
.failsafe #loader{display:none}
.failsafe{overflow:auto!important}

/* loader */
#loader{position:fixed;inset:0;z-index:300;background:#05060a;display:flex;flex-direction:column;justify-content:space-between;padding:30px clamp(18px,3vw,40px);transition:transform 1.1s cubic-bezier(.76,0,.24,1)}
#loader.done{transform:translateY(-101%);pointer-events:none}
.lg{display:flex;align-items:center;gap:12px;font-family:"Inter Tight",sans-serif;font-weight:600;font-size:1.3rem}
.lc{font-family:"Inter Tight",sans-serif;font-weight:600;font-size:clamp(5rem,18vw,15rem);line-height:.8;letter-spacing:-.05em;color:#fff}
.lbar{position:absolute;left:0;right:0;bottom:0;height:3px;background:rgba(255,255,255,.08)}
.lbar i{display:block;height:100%;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,var(--acc),var(--warm))}
.dot{display:inline-block;width:20px;height:20px;border-radius:50%;background:radial-gradient(circle at 32% 30%,#fff,var(--acc) 45%,#1d2147)}

#prog{position:fixed;top:0;left:0;height:2px;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,var(--acc),var(--warm));z-index:100}

/* nav */
.nav{position:fixed;inset:0 0 auto;z-index:60;display:flex;justify-content:space-between;align-items:center;padding:20px clamp(18px,3vw,40px);transition:background .4s,padding .4s,border-color .4s;border-bottom:1px solid transparent}
.nav.scrolled{background:rgba(6,7,10,.62);backdrop-filter:blur(16px) saturate(1.4);padding-block:12px;border-color:var(--line)}
.logo{display:flex;align-items:center;gap:10px;font-family:"Inter Tight",sans-serif;font-weight:600;font-size:1.25rem;letter-spacing:-.03em}
.nl{display:flex;gap:4px;position:absolute;left:50%;transform:translateX(-50%)}
.nl a{padding:8px 16px;border-radius:999px;color:var(--mut);font-size:.92rem;transition:color .25s,background .25s}
.nl a:hover{color:#fff;background:var(--glass)}
.nr{display:flex;align-items:center;gap:14px}
kbd{font:500 .72rem/1 ui-monospace,Menlo,monospace;color:var(--mut);border:1px solid var(--line);border-radius:7px;padding:5px 8px;background:var(--glass)}
.btn{display:inline-flex;align-items:center;gap:10px;padding:13px 24px;border-radius:999px;font-weight:600;font-size:.95rem;border:1px solid var(--line);background:var(--glass);transition:transform .35s var(--ease),background .3s,box-shadow .3s}
.btn:hover{transform:translateY(-2px);background:rgba(255,255,255,.1)}
.btn.pr{background:#f3f4f8;color:#06070a;border-color:transparent}
.btn.pr:hover{background:#fff;box-shadow:0 12px 40px -10px rgba(142,162,255,.7)}
.btn.sm{padding:9px 18px;font-size:.88rem}
@media(max-width:900px){.nl,.nr kbd{display:none}}

/* hero */
.hero{position:relative;overflow:clip;min-height:100svh;display:grid;place-items:center;text-align:center;padding:130px 6vw 100px}
.hc{position:relative;z-index:3;max-width:1180px;overflow-x:clip}
.hc::before{content:"";position:absolute;inset:-12% -8%;z-index:-1;background:radial-gradient(closest-side,rgba(6,7,10,.5),transparent)}
.pill{display:inline-flex;align-items:center;gap:10px;padding:8px 16px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.05);backdrop-filter:blur(10px);font-size:.84rem;color:var(--mut);margin-bottom:30px}
.pill i{width:7px;height:7px;border-radius:50%;background:#5dffb0;box-shadow:0 0 12px #5dffb0}
.pill b{color:var(--fg);font-weight:500}
.hero h1{font-size:clamp(3.1rem,9.4vw,9.2rem);margin-bottom:28px}
.hero h1 .ser{font-size:1.04em}
.hero .lead{margin:0 auto}
.ask{display:flex;align-items:center;gap:10px;width:min(700px,92vw);margin:38px auto 0;padding:9px 9px 9px 24px;border-radius:999px;background:rgba(16,18,26,.72);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.14);box-shadow:0 30px 90px -30px rgba(142,162,255,.45);transition:border-color .3s,box-shadow .3s}
.ask:focus-within{border-color:rgba(142,162,255,.75);box-shadow:0 30px 100px -24px rgba(142,162,255,.75)}
.ask .i{color:var(--acc);width:1.35em;height:1.35em}
.ask input{flex:1;min-width:0;background:none;border:0;outline:0;font-size:1.05rem;padding:12px 4px}
.ask input::placeholder{color:#6f7589}
.go{flex:none;width:50px;height:50px;border-radius:50%;background:#f3f4f8;color:#06070a;display:grid;place-items:center;transition:transform .3s var(--ease)}
.go:hover{transform:scale(1.08) rotate(-6deg)}
.go .i{color:#06070a;stroke-width:2.2}
.chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.hero .chips{margin-top:18px}
.chip{padding:9px 16px;border-radius:999px;border:1px solid var(--line);background:var(--glass);font-size:.86rem;color:#c9cddb;transition:background .25s,border-color .25s,transform .3s var(--ease),color .25s}
.chip:hover{background:rgba(142,162,255,.16);border-color:rgba(142,162,255,.6);color:#fff;transform:translateY(-2px)}
.hb{position:absolute;left:0;right:0;bottom:28px;display:flex;justify-content:space-between;gap:20px;padding:0 clamp(18px,3vw,40px);z-index:3}
.hb span{display:flex;align-items:center;gap:12px}
.hb span:first-child::before{content:"";width:1px;height:34px;background:linear-gradient(var(--acc),transparent);animation:drip 2s ease-in-out infinite}
@keyframes drip{0%{transform:scaleY(0);transform-origin:top}50%{transform:scaleY(1);transform-origin:top}51%{transform-origin:bottom}100%{transform:scaleY(0);transform-origin:bottom}}
@media(min-width:701px){.hb{padding-right:clamp(250px,20vw,310px)}}
@media(max-width:700px){.hc::before{inset:-8% 0;background:radial-gradient(closest-side,rgba(6,7,10,.78),transparent)}}
@media(max-width:700px){.hb span:last-child{display:none}.hero{padding-top:120px}.hero .chips .chip:nth-child(3){display:none}}

/* marquee */
.marq{position:relative;z-index:3;overflow:hidden;border-block:1px solid var(--line);padding:26px 0;background:rgba(6,7,10,.7);backdrop-filter:blur(6px)}
.track{display:flex;gap:56px;width:max-content;animation:marq 40s linear infinite;align-items:center}
.track span{font-family:"Inter Tight",sans-serif;font-size:1.5rem;font-weight:600;letter-spacing:-.02em;color:#555b73;white-space:nowrap}
.track em{color:var(--acc);font-style:normal;opacity:.7}
@keyframes marq{to{transform:translateX(-50%)}}

/* story */
.story{position:relative;z-index:3;height:560vh}
.sticky{position:sticky;top:0;height:100svh;overflow:hidden}
.st-top{position:absolute;left:clamp(18px,5vw,80px);right:clamp(18px,5vw,80px);top:96px;display:flex;justify-content:space-between}
.st-top b{color:#fff;font-weight:600}
.chap{position:absolute;left:clamp(18px,5vw,80px);bottom:clamp(50px,11vh,120px);max-width:min(500px,86vw);opacity:0;transform:translateY(30px);pointer-events:none;transition:opacity .8s ease,transform 1s var(--ease)}
.chap.on{opacity:1;transform:none}
.chap::before{content:"";position:absolute;inset:-50px -70px -40px -80px;z-index:-1;background:radial-gradient(closest-side,rgba(6,7,10,.78),transparent)}
.chap .n{display:block;font-family:"Inter Tight",sans-serif;font-weight:700;font-size:clamp(4.5rem,11vw,10rem);line-height:.85;color:transparent;-webkit-text-stroke:1px rgba(255,255,255,.4);margin-bottom:18px;letter-spacing:-.05em}
.chap h3{font-size:clamp(2rem,4.2vw,3.6rem);margin-bottom:16px}
.chap p{color:#a7acbd;font-size:1.05rem;max-width:42ch}
.rail{position:absolute;right:clamp(18px,4vw,60px);top:50%;transform:translateY(-50%);display:grid;gap:22px}
.rail span{display:flex;gap:14px;align-items:center;justify-content:flex-end;color:#5f657a;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;transition:color .5s}
.rail span::after{content:"";width:22px;height:1px;background:currentColor;transition:width .6s var(--ease),background .5s}
.rail span.on{color:#fff}.rail span.on::after{width:60px;background:var(--acc)}
.sbar{position:absolute;left:0;right:0;bottom:0;height:2px;background:rgba(255,255,255,.06)}
.sbar i{display:block;height:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,var(--acc),var(--warm))}
@media(max-width:820px){.rail{display:none}.chap{background:linear-gradient(0deg,rgba(6,7,10,.85),rgba(6,7,10,0));padding:30px 0 0}}

/* bento */
.bento{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-top:64px}
.card{position:relative;padding:30px;border-radius:30px;border:1px solid var(--line);background:linear-gradient(165deg,rgba(255,255,255,.065),rgba(255,255,255,.02));overflow:hidden;transition:transform .35s var(--ease),border-color .3s;will-change:transform;display:flex;flex-direction:column}
.card::before{content:"";position:absolute;inset:0;background:radial-gradient(560px circle at var(--mx,50%) var(--my,0%),rgba(142,162,255,.2),transparent 45%);opacity:0;transition:opacity .35s;pointer-events:none}
.card:hover{border-color:rgba(142,162,255,.45)}.card:hover::before{opacity:1}
.card h3{font-family:"Inter Tight",sans-serif;font-size:1.55rem;letter-spacing:-.03em;line-height:1.1;margin-bottom:10px}
.card>p{color:var(--mut);max-width:38ch}
.card .vis{margin-top:auto;padding-top:26px}
.s4{grid-column:span 4}.s2{grid-column:span 2}
@media(max-width:960px){.bento{grid-template-columns:1fr 1fr}.s4{grid-column:span 2}.s2{grid-column:span 1}}
@media(max-width:620px){.bento{grid-template-columns:1fr}.s4,.s2{grid-column:auto}}
.mock{border:1px solid var(--line);border-radius:20px;background:rgba(6,7,10,.55);padding:18px;display:grid;gap:12px}
.mu{justify-self:end;background:rgba(142,162,255,.2);border:1px solid rgba(142,162,255,.3);padding:9px 15px;border-radius:16px 16px 4px 16px;font-size:.9rem}
.mb{display:grid;gap:9px;padding:6px 4px}
.ln{height:9px;border-radius:5px;background:linear-gradient(90deg,var(--acc),rgba(255,199,160,.6));width:0;animation:ln 5s ease-in-out infinite}
.ln:nth-child(1){--w:92%}.ln:nth-child(2){--w:78%;animation-delay:.35s}.ln:nth-child(3){--w:55%;animation-delay:.7s}
@keyframes ln{0%{width:0;opacity:1}30%,80%{width:var(--w);opacity:1}100%{width:var(--w);opacity:0}}
.lat{display:flex;gap:8px;align-items:center;font-size:.78rem;color:var(--mut)}
.lat b{color:#5dffb0;font-weight:600}
.lang{position:relative;height:84px}
.lang span{position:absolute;inset:0;display:flex;align-items:center;font-family:"Inter Tight","Noto Naskh Arabic",sans-serif;font-weight:600;font-size:2.3rem;letter-spacing:-.03em;opacity:0;animation:cyc 12.5s infinite;animation-delay:calc(var(--i)*2.5s)}
@keyframes cyc{0%{opacity:0;transform:translateY(16px)}3%,17%{opacity:1;transform:none}20%,100%{opacity:0;transform:translateY(-16px)}}
.tg{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--line);font-size:.92rem;color:#c6cad8}
.tg:last-child{border:0}
.sw{width:42px;height:24px;border-radius:99px;background:#2a2e40;position:relative;flex:none}
.sw::after{content:"";position:absolute;left:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.3s}
.sw.on{background:var(--acc)}.sw.on::after{transform:translateX(18px)}
.mods{display:grid;gap:8px}
.mod{display:flex;justify-content:space-between;align-items:center;padding:11px 15px;border-radius:14px;border:1px solid var(--line);font-size:.92rem;color:#c6cad8}
.mod small{color:var(--mut)}
.mod.on{border-color:rgba(142,162,255,.7);background:rgba(142,162,255,.12);color:#fff}
.sl{display:grid;gap:6px;margin-bottom:16px;font-size:.84rem;color:var(--mut)}
.sl div{display:flex;justify-content:space-between}
.rl{height:6px;border-radius:4px;background:#252a3c;position:relative}
.rl i{position:absolute;left:0;top:0;bottom:0;border-radius:4px;background:linear-gradient(90deg,var(--acc),var(--warm));animation:fill 6s ease-in-out infinite alternate}
.rl i::after{content:"";position:absolute;right:-8px;top:50%;width:16px;height:16px;margin-top:-8px;border-radius:50%;background:#fff;box-shadow:0 0 0 4px rgba(142,162,255,.3)}
@keyframes fill{from{width:var(--a,30%)}to{width:var(--b,80%)}}

/* horizontal use-cases */
.hs{position:relative;z-index:3;height:420vh}
.hsx{position:sticky;top:0;height:100svh;overflow:hidden;display:flex;flex-direction:column;justify-content:center;gap:clamp(24px,5vh,56px)}
.hh{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;padding:0 clamp(18px,5vw,80px)}
.hrow{display:flex;gap:20px;padding:0 clamp(18px,5vw,80px);width:max-content;will-change:transform}
.uc{flex:none;width:min(460px,82vw);min-height:min(500px,58vh);padding:32px;border-radius:32px;border:1px solid var(--line);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.02));backdrop-filter:blur(14px);display:flex;flex-direction:column;justify-content:space-between;gap:24px}
.uc .tag{display:inline-flex;align-items:center;gap:8px;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--acc)}
.uc h3{font-family:"Inter Tight",sans-serif;font-size:clamp(1.8rem,3vw,2.5rem);letter-spacing:-.04em;line-height:1;margin:14px 0 12px}
.uc p.t{color:var(--mut)}
.hbar{margin:0 clamp(18px,5vw,80px);height:2px;background:rgba(255,255,255,.08);border-radius:2px}
.hbar i{display:block;height:100%;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,var(--acc),var(--warm))}

/* stats, quotes, faq */
.stats{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stat{padding:50px 24px;border-right:1px solid var(--line)}
.stat:last-child{border:0}
.stat b{display:block;font-family:"Inter Tight",sans-serif;font-weight:600;letter-spacing:-.05em;font-size:clamp(2.8rem,6vw,5.4rem);line-height:1}
.stat span{color:var(--mut)}
@media(max-width:820px){.stats{grid-template-columns:1fr 1fr}.stat:nth-child(2){border-right:0}.stat:nth-child(-n+2){border-bottom:1px solid var(--line)}}
.quotes{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:60px}
.q{padding:34px;border-radius:30px;border:1px solid var(--line);background:var(--glass);display:flex;flex-direction:column;justify-content:space-between;gap:34px}
.q p{font-family:"Inter Tight",sans-serif;font-size:1.35rem;letter-spacing:-.02em;line-height:1.3;font-weight:500}
.who{display:flex;align-items:center;gap:12px;color:var(--mut);font-size:.9rem}
.who i{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--acc),var(--warm))}
.who b{display:block;color:#fff;font-weight:500}
@media(max-width:900px){.quotes{grid-template-columns:1fr}}
.faq{max-width:900px;margin-top:56px;border-top:1px solid var(--line)}
details{border-bottom:1px solid var(--line);padding:26px 4px}
summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;gap:24px;font-family:"Inter Tight",sans-serif;font-size:clamp(1.2rem,2.2vw,1.6rem);font-weight:500;letter-spacing:-.02em}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";font-weight:300;font-size:2rem;line-height:1;color:var(--acc);transition:transform .4s var(--ease)}
details[open] summary::after{transform:rotate(135deg)}
details p{color:var(--mut);margin-top:14px;max-width:62ch}

/* cta + footer */
.cta{text-align:center;padding-top:clamp(120px,22vh,260px);padding-bottom:clamp(100px,18vh,200px)}
.cta h2{margin:0 auto;max-width:12ch;font-size:clamp(3rem,9vw,8rem)}
.cta .lead{margin:24px auto 0}
.cta .ask{margin-top:36px}
footer{background:rgba(6,7,10,.9);border-top:1px solid var(--line);padding:56px 0 0;overflow:hidden}
.fr{display:flex;justify-content:space-between;gap:30px;flex-wrap:wrap;color:var(--mut);font-size:.92rem}
.fr nav{display:flex;gap:26px;flex-wrap:wrap}
.fr a:hover{color:#fff}
.mega{font-family:"Inter Tight",sans-serif;font-weight:700;font-size:clamp(7rem,27vw,24rem);letter-spacing:-.07em;line-height:.74;text-align:center;margin-top:50px;background:linear-gradient(180deg,rgba(255,255,255,.22),rgba(255,255,255,0) 85%);-webkit-background-clip:text;background-clip:text;color:transparent;user-select:none;transform:translateY(12%)}

/* cursor */
.cur-dot,.cur-ring{position:fixed;left:0;top:0;pointer-events:none;z-index:500;display:none}
.has-cursor .cur-dot,.has-cursor .cur-ring{display:block}
.cur-dot{width:7px;height:7px;margin:-3.5px 0 0 -3.5px;border-radius:50%;background:#fff;mix-blend-mode:difference}
.cur-ring{width:40px;height:40px;margin:-20px 0 0 -20px;border-radius:50%;border:1px solid rgba(255,255,255,.45);transition:width .3s var(--ease),height .3s var(--ease),margin .3s var(--ease),background .3s}
.cur-ring.big{width:72px;height:72px;margin:-36px 0 0 -36px;background:rgba(142,162,255,.14)}
.has-cursor,.has-cursor a,.has-cursor button,.has-cursor summary,.has-cursor .chip{cursor:none}
.has-cursor input,.has-cursor textarea{cursor:text}

/* chat */
#launcher{position:fixed;right:24px;bottom:24px;z-index:80;height:60px;padding:0 24px 0 18px;border-radius:999px;display:flex;align-items:center;gap:12px;background:#f3f4f8;color:#06070a;font-weight:600;box-shadow:0 20px 60px -12px rgba(142,162,255,.6);transition:transform .4s var(--ease),opacity .3s}
#launcher:hover{transform:translateY(-3px) scale(1.03)}
#launcher .dot{width:26px;height:26px}
body.chat-open #launcher{opacity:0;pointer-events:none;transform:scale(.8)}
@media(max-width:560px){#launcher span.t{display:none}#launcher{padding:0 16px}}
#chat{position:fixed;right:24px;bottom:24px;z-index:90;width:min(440px,calc(100vw - 24px));height:min(700px,calc(100svh - 48px));display:flex;flex-direction:column;border-radius:30px;border:1px solid rgba(255,255,255,.14);background:rgba(11,13,19,.94);backdrop-filter:blur(28px) saturate(1.5);box-shadow:0 50px 140px -20px rgba(0,0,0,.9),0 0 0 1px rgba(142,162,255,.1);transform-origin:bottom right;opacity:0;visibility:hidden;pointer-events:none;transform:translateY(24px) scale(.94);transition:opacity .35s,transform .55s var(--ease),visibility .35s;overflow:hidden}
#chat.open{opacity:1;visibility:visible;pointer-events:auto;transform:none}
@media(max-width:560px){#chat{right:8px;left:8px;bottom:8px;width:auto;height:calc(100svh - 16px);border-radius:26px}}
.ch{display:flex;align-items:center;gap:14px;padding:18px 20px;border-bottom:1px solid var(--line)}
.orb{position:relative;width:42px;height:42px;border-radius:50%;flex:none;background:conic-gradient(from 0deg,var(--acc),var(--warm),var(--acc));animation:spin 6s linear infinite}
.orb::after{content:"";position:absolute;inset:4px;border-radius:50%;background:radial-gradient(circle at 32% 30%,#fff,var(--acc) 42%,#1b1f3d)}
@keyframes spin{to{transform:rotate(360deg)}}
.ch b{display:block;font-family:"Inter Tight",sans-serif;font-size:1.1rem;letter-spacing:-.02em;line-height:1.2}
.ch small{display:flex;align-items:center;gap:7px;color:var(--mut);font-size:.78rem}
.ch small i{width:7px;height:7px;border-radius:50%;background:#5dffb0;box-shadow:0 0 10px #5dffb0}
.acts{margin-left:auto;display:flex;gap:8px}
.acts button{width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:var(--glass);display:grid;place-items:center;transition:background .2s}
.acts button:hover{background:rgba(255,255,255,.12)}
#msgs{flex:1;overflow-y:auto;padding:10px 20px 4px;scroll-behavior:smooth;overscroll-behavior:contain}
#msgs::-webkit-scrollbar{width:6px}#msgs::-webkit-scrollbar-thumb{background:#2a2e40;border-radius:3px}
.msg{display:flex;gap:10px;margin:16px 0;animation:pop .5s var(--ease)}
@keyframes pop{from{opacity:0;transform:translateY(12px)}}
.msg .av{width:28px;height:28px;margin-top:2px;flex:none;border-radius:50%;background:radial-gradient(circle at 32% 30%,#fff,var(--acc) 45%,#1d2147)}
.bub{max-width:84%;padding:12px 16px;border-radius:20px;font-size:.96rem;line-height:1.55;overflow-wrap:anywhere}
.msg.bot .bub{background:rgba(255,255,255,.06);border:1px solid var(--line);border-top-left-radius:6px}
.msg.user{justify-content:flex-end}
.msg.user .bub{background:#f3f4f8;color:#0a0c12;border-bottom-right-radius:6px;font-weight:500}
.bub code{background:rgba(255,255,255,.12);padding:1px 6px;border-radius:6px;font-size:.88em}
.msg.user .bub code{background:rgba(0,0,0,.1)}
.typing{display:flex;gap:5px;padding:6px 2px}
.typing i{width:7px;height:7px;border-radius:50%;background:var(--mut);animation:dots 1.2s infinite}
.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes dots{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
#chips{padding:6px 20px 14px;justify-content:flex-start}
#chatForm{display:flex;align-items:flex-end;gap:10px;margin:0 16px;padding:8px 8px 8px 18px;border-radius:26px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);transition:border-color .3s,box-shadow .3s}
#chatForm:focus-within{border-color:rgba(142,162,255,.7);box-shadow:0 0 0 4px rgba(142,162,255,.14)}
#chatInput{flex:1;min-width:0;resize:none;background:none;border:0;outline:0;padding:10px 0;max-height:120px;line-height:1.45;font-size:.98rem}
#chatInput::placeholder{color:#6f7589}
#sendBtn{width:42px;height:42px;border-radius:50%;background:#f3f4f8;color:#06070a;display:grid;place-items:center;flex:none;transition:transform .3s var(--ease),opacity .2s}
#sendBtn .i{stroke-width:2.2}
#sendBtn:hover:not(:disabled){transform:scale(1.08)}
#sendBtn:disabled{opacity:.25;cursor:not-allowed}
.fine{text-align:center;color:#5f657a;font-size:.72rem;padding:10px 12px 14px}
.reduce *,.reduce *::before,.reduce *::after{animation:none!important;transition-duration:.01ms!important;scroll-behavior:auto!important}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/><path d="M19 16v4M17 18h4"/></symbol>
  <symbol id="i-up" viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></symbol>
  <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
  <symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
  <symbol id="i-refresh" viewBox="0 0 24 24"><path d="M20 11a8 8 0 10-2.3 5.7M20 4v7h-7"/></symbol>
</svg>

<div id="loader" aria-hidden="true">
  <div class="lg"><span class="dot"></span>Lumen</div>
  <div class="lc" id="lc">0%</div>
  <div class="lbar"><i id="lb"></i></div>
</div>
<div id="prog"></div>
<div class="cur-dot"></div><div class="cur-ring"></div>
<div class="aurora"></div>
<canvas id="gl" aria-hidden="true"></canvas>
<div class="fallback" aria-hidden="true"></div>
<a class="skip" href="#main">Skip to content</a>

<header class="nav" id="nav">
  <a class="logo" href="#top"><span class="dot"></span>Lumen</a>
  <nav class="nl" aria-label="Main"><a href="#story">How it thinks</a><a href="#features">Features</a><a href="#usecases">Use cases</a><a href="#faq">FAQ</a></nav>
  <div class="nr"><kbd>Ctrl K</kbd><button class="btn pr sm" data-open>Try Lumen</button></div>
</header>

<main id="main">
  <section class="hero" id="top">
    <div class="hc">
      <div class="pill rvh" style="--k:0"><i></i><span><b>Lumen 2.0</b> &middot; now fluent in 95 languages</span></div>
      <h1 class="d" data-split>Talk to an AI<br>that feels <span class="ser gt">alive.</span></h1>
      <p class="lead rvh" style="--k:1">An assistant with a living interface. Ask in your own language and watch it think, in real time.</p>
      <form class="ask rvh" id="heroForm" style="--k:2" autocomplete="off">
        <svg class="i"><use href="#i-spark"/></svg>
        <input id="heroInput" maxlength="500" placeholder="Ask Lumen anything..." aria-label="Ask Lumen anything">
        <button class="go" type="submit" aria-label="Ask"><svg class="i"><use href="#i-up"/></svg></button>
      </form>
      <div class="chips rvh" style="--k:3">
        <button class="chip" type="button">What can you do?</button>
        <button class="chip" type="button">Explain AI simply</button>
        <button class="chip" type="button">Give me a business idea</button>
      </div>
    </div>
    <div class="hb lab"><span>Scroll to explore</span><span>Move your cursor</span></div>
  </section>

  <div class="marq" aria-label="Trusted by teams at">
    <div class="track">
      <span>NORTHWIND</span><em>&#10022;</em><span>Acme Labs</span><em>&#10022;</em><span>VERTEX</span><em>&#10022;</em><span>Helix</span><em>&#10022;</em><span>Paperplane</span><em>&#10022;</em><span>QUANTA</span><em>&#10022;</em><span>Brightly</span><em>&#10022;</em><span>ORBITAL</span><em>&#10022;</em>
      <span>NORTHWIND</span><em>&#10022;</em><span>Acme Labs</span><em>&#10022;</em><span>VERTEX</span><em>&#10022;</em><span>Helix</span><em>&#10022;</em><span>Paperplane</span><em>&#10022;</em><span>QUANTA</span><em>&#10022;</em><span>Brightly</span><em>&#10022;</em><span>ORBITAL</span><em>&#10022;</em>
    </div>
  </div>

  <section class="story" id="story" aria-label="How Lumen thinks">
    <div class="sticky">
      <div class="st-top lab"><span>How Lumen thinks</span><span><b id="sIdx">01</b> / 04</span></div>
      <div class="chap on"><span class="n">01</span><h3 class="d">A mind <span class="ser gt">in motion.</span></h3><p>Every conversation starts with a living core. Forty thousand points of light, each one a small piece of the thought.</p></div>
      <div class="chap"><span class="n">02</span><h3 class="d">It <span class="ser gt">listens.</span></h3><p>Your words become waves. Lumen reads tone, context and intent, in 95 languages, before it answers.</p></div>
      <div class="chap"><span class="n">03</span><h3 class="d">It <span class="ser gt">reasons.</span></h3><p>Ideas loop, connect and fold into each other. You get an answer that is considered, not just fast.</p></div>
      <div class="chap"><span class="n">04</span><h3 class="d">It grows <span class="ser gt">with you.</span></h3><p>The more you talk, the more it understands. A small spark becomes a whole galaxy of help.</p></div>
      <div class="rail lab"><span class="on">Core</span><span>Listen</span><span>Reason</span><span>Grow</span></div>
      <div class="sbar"><i id="sbar"></i></div>
    </div>
  </section>

  <section class="sec veil" id="features">
    <div class="wrap">
      <span class="lab eyebrow rv">Features</span>
      <h2 class="d" data-split>Designed to feel <span class="ser gt">effortless.</span></h2>
      <div class="bento">
        <article class="card tilt s4 rv">
          <h3>Answers that stream in, instantly.</h3>
          <p>Replies appear word by word while the 3D core pulses with every thought, so you always know what Lumen is doing.</p>
          <div class="vis"><div class="mock"><div class="mu">Summarise my meeting in 3 points</div><div class="mb"><div class="ln"></div><div class="ln"></div><div class="ln"></div></div><div class="lat"><b>0.8s</b> first word &middot; streaming</div></div></div>
        </article>
        <article class="card tilt s2 rv" style="--d:.1s">
          <h3>Speaks your language.</h3>
          <p>Write in any of 95 languages. Lumen replies in the same one.</p>
          <div class="vis"><div class="lang" aria-hidden="true"><span style="--i:0">Hello</span><span style="--i:1">السلام علیکم</span><span style="--i:2">Hola</span><span style="--i:3">Bonjour</span><span style="--i:4">你好</span></div></div>
        </article>
        <article class="card tilt s2 rv">
          <h3>Private by design.</h3>
          <p>You decide what is kept.</p>
          <div class="vis"><div class="tg"><span>Save chat history</span><i class="sw on"></i></div><div class="tg"><span>Use chats for training</span><i class="sw"></i></div></div>
        </article>
        <article class="card tilt s2 rv" style="--d:.1s">
          <h3>Powered by Claude.</h3>
          <p>A top-tier model, tuned for clear answers.</p>
          <div class="vis"><div class="mods"><div class="mod on">Sonnet <small>Balanced</small></div><div class="mod">Haiku <small>Fastest</small></div></div></div>
        </article>
        <article class="card tilt s2 rv" style="--d:.2s">
          <h3>Make it yours.</h3>
          <p>Tune tone and length.</p>
          <div class="vis"><div class="sl"><div><span>Tone</span><span>Friendly</span></div><div class="rl"><i style="--a:35%;--b:85%"></i></div></div><div class="sl"><div><span>Length</span><span>Short</span></div><div class="rl"><i style="--a:70%;--b:30%"></i></div></div></div>
        </article>
      </div>
    </div>
  </section>

  <section class="hs" id="usecases" aria-label="Use cases">
    <div class="hsx">
      <div class="hh">
        <div><span class="lab eyebrow">Use cases</span><h2 class="d" style="max-width:12ch">Built for <span class="ser gt">every team.</span></h2></div>
        <p class="lead" style="max-width:34ch">One assistant, many jobs. Keep scrolling.</p>
      </div>
      <div class="hrow" id="hrow">
        <article class="uc"><div><span class="tag">01 &middot; Support</span><h3>Answers at 3 a.m.</h3><p class="t">Resolve common questions instantly, in the customer's own language, and hand off only the hard ones.</p></div><div class="mock"><div class="mu">Where is my order?</div><div class="mb"><div class="ln"></div><div class="ln"></div></div></div></article>
        <article class="uc"><div><span class="tag">02 &middot; Learning</span><h3>A patient tutor.</h3><p class="t">Explains tricky topics step by step, quizzes you, and never gets tired of "why?".</p></div><div class="mock"><div class="mu">Explain photosynthesis simply</div><div class="mb"><div class="ln"></div><div class="ln"></div></div></div></article>
        <article class="uc"><div><span class="tag">03 &middot; Sales</span><h3>Warm leads, faster.</h3><p class="t">Qualifies visitors, answers product questions and books the meeting while your team sleeps.</p></div><div class="mock"><div class="mu">Do you offer a team plan?</div><div class="mb"><div class="ln"></div><div class="ln"></div></div></div></article>
        <article class="uc"><div><span class="tag">04 &middot; Code</span><h3>A pair programmer.</h3><p class="t">Reads errors, suggests fixes and explains what the code does in plain words.</p></div><div class="mock"><div class="mu">Why is my loop never ending?</div><div class="mb"><div class="ln"></div><div class="ln"></div></div></div></article>
      </div>
      <div class="hbar"><i id="hbar"></i></div>
    </div>
  </section>

  <section class="sec veil">
    <div class="wrap">
      <div class="stats rv">
        <div class="stat"><b data-count="2" data-suf="M+">2M+</b><span>Conversations</span></div>
        <div class="stat"><b data-count="95" data-suf="+">95+</b><span>Languages</span></div>
        <div class="stat"><b data-count="99" data-suf="%">99%</b><span>Uptime</span></div>
        <div class="stat"><b data-count="4.9" data-suf="">4.9</b><span>User rating</span></div>
      </div>
      <div class="quotes">
        <figure class="q rv"><p>&ldquo;It answered my customers in Urdu and English without me changing a thing. Support tickets dropped by half.&rdquo;</p><figcaption class="who"><i></i><span><b>Hamza R.</b>Founder, Northwind</span></figcaption></figure>
        <figure class="q rv" style="--d:.1s"><p>&ldquo;The interface alone made people stay. They just wanted to see what the particles would do next.&rdquo;</p><figcaption class="who"><i></i><span><b>Maryam S.</b>Design lead, Vertex</span></figcaption></figure>
        <figure class="q rv" style="--d:.2s"><p>&ldquo;Fast, polite and honest when it does not know. That is exactly what we needed.&rdquo;</p><figcaption class="who"><i></i><span><b>Talha A.</b>Product manager, Helix</span></figcaption></figure>
      </div>
    </div>
  </section>

  <section class="sec" id="faq">
    <div class="wrap">
      <span class="lab eyebrow rv">FAQ</span>
      <h2 class="d" data-split>Questions, <span class="ser gt">answered.</span></h2>
      <div class="faq rv">
        <details><summary>Is Lumen free to try?</summary><p>Yes. Open the chat and start talking, no account needed.</p></details>
        <details><summary>Which languages does it support?</summary><p>More than 95, including English, Urdu, Arabic and Spanish.</p></details>
        <details><summary>Is my data safe?</summary><p>Conversations are private and never used for advertising.</p></details>
        <details><summary>Can I add it to my own website?</summary><p>Yes. Lumen is a single chat widget that can be dropped into any site.</p></details>
      </div>
    </div>
  </section>

  <section class="sec cta" id="cta">
    <div class="wrap">
      <h2 class="d" data-split>Say hello to <span class="ser gt">Lumen.</span></h2>
      <p class="lead rv">Start a conversation in under five seconds.</p>
      <form class="ask rv" id="ctaForm" autocomplete="off">
        <svg class="i"><use href="#i-spark"/></svg>
        <input id="ctaInput" maxlength="500" placeholder="Type your first message..." aria-label="Type your first message">
        <button class="go" type="submit" aria-label="Send"><svg class="i"><use href="#i-up"/></svg></button>
      </form>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <div class="fr"><a class="logo" href="#top"><span class="dot"></span>Lumen</a><nav aria-label="Footer"><a href="#story">How it thinks</a><a href="#features">Features</a><a href="#usecases">Use cases</a><a href="#faq">FAQ</a></nav><span>&copy; 2026 Lumen. Demo project.</span></div>
  </div>
  <div class="mega" aria-hidden="true">LUMEN</div>
</footer>

<button id="launcher" aria-label="Open chat" aria-controls="chat"><span class="dot"></span><span class="t">Chat with Lumen</span></button>

<section id="chat" role="dialog" aria-label="Chat with Lumen" aria-hidden="true">
  <div class="ch">
    <span class="orb"></span>
    <div><b>Lumen</b><small id="mode"><i></i><span>Online</span></small></div>
    <div class="acts">
      <button id="newChat" aria-label="New chat"><svg class="i"><use href="#i-refresh"/></svg></button>
      <button id="closeChat" aria-label="Close chat"><svg class="i"><use href="#i-close"/></svg></button>
    </div>
  </div>
  <div id="msgs" aria-live="polite"></div>
  <div class="chips" id="chips">
    <button class="chip" type="button">What can you do?</button>
    <button class="chip" type="button">Explain AI simply</button>
    <button class="chip" type="button">Give me a business idea</button>
  </div>
  <form id="chatForm" autocomplete="off">
    <textarea id="chatInput" rows="1" maxlength="500" placeholder="Message Lumen..." aria-label="Your message"></textarea>
    <button id="sendBtn" type="submit" aria-label="Send" disabled><svg class="i"><use href="#i-up"/></svg></button>
  </form>
  <p class="fine">Lumen can make mistakes. Check important info.</p>
</section>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js"></script>
<script>
(() => {
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const root = document.documentElement;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const fine = matchMedia("(hover:hover) and (pointer:fine)").matches;
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => t * t * (3 - 2 * t);
if (reduce) root.classList.add("reduce");

/* ---------- split text into words ---------- */
$$("[data-split]").forEach((el) => {
  let n = 0;
  const walk = (node) => {
    [...node.childNodes].forEach((c) => {
      if (c.nodeType === 3) {
        const frag = document.createDocumentFragment();
        c.textContent.split(/(\s+)/).forEach((p) => {
          if (!p) return;
          if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(" ")); return; }
          const w = document.createElement("span"); w.className = "wd";
          const s = document.createElement("span"); s.style.setProperty("--i", n++); s.textContent = p;
          w.appendChild(s); frag.appendChild(w);
        });
        node.replaceChild(frag, c);
      } else if (c.nodeType === 1 && c.tagName !== "BR") walk(c);
    });
  };
  walk(el);
});

/* ---------- reveal on scroll ---------- */
const io = "IntersectionObserver" in window ? new IntersectionObserver((list) => list.forEach((e) => {
  if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
}), { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }) : null;
$$(".rv, [data-split]").forEach((el) => { if (el.closest(".hero")) return; io ? io.observe(el) : el.classList.add("in"); });

/* count-up numbers */
const cio = "IntersectionObserver" in window ? new IntersectionObserver((list) => list.forEach((e) => {
  if (!e.isIntersecting) return; cio.unobserve(e.target);
  const el = e.target, end = parseFloat(el.dataset.count), suf = el.dataset.suf || "", dec = String(end).includes(".") ? 1 : 0, t0 = performance.now();
  const step = (now) => {
    const k = clamp((now - t0) / 1800), v = end * (1 - Math.pow(1 - k, 3));
    el.textContent = v.toFixed(dec) + suf;
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}), { threshold: 0.5 }) : null;
$$("[data-count]").forEach((el) => cio && cio.observe(el));

/* ---------- smooth scroll ---------- */
let lenis = null;
if (window.Lenis && !reduce) lenis = new Lenis({ lerp: 0.1 });
$$('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
  const t = $(a.getAttribute("href")); if (!t) return;
  e.preventDefault();
  lenis ? lenis.scrollTo(t, { offset: 0 }) : t.scrollIntoView({ behavior: "smooth" });
}));

/* ---------- 3D particle universe ---------- */
const S = { think: 0, thinkT: 0, pulse: 0, intro: reduce ? 1 : 0, morph: 0, opacity: 1, scale: 1, rot: 0, spin: 0 };
window.orbSet = (s) => { S.thinkT = s === "thinking" ? 1 : 0; };
window.orbKick = (v = 0.4) => { S.pulse = Math.min(S.pulse + v, 1.4); };

const VS = `
attribute vec3 aP0; attribute vec3 aP1; attribute vec3 aP2; attribute vec3 aP3; attribute vec4 aR;
uniform float uTime; uniform float uMorph; uniform float uIntro; uniform float uPx; uniform float uRot;
uniform float uAmp; uniform float uPulse; uniform float uScale; uniform float uOpacity; uniform float uMouseStr;
uniform vec3 uMouse; uniform vec3 uOffset; uniform vec3 uColA; uniform vec3 uColB;
varying vec3 vC; varying float vA;
vec3 pick(float k){ return k<0.5 ? aP0 : (k<1.5 ? aP1 : (k<2.5 ? aP2 : aP3)); }
void main(){
  float m = clamp(uMorph, 0.0, 3.0);
  float i = min(floor(m), 2.0);
  float f = m - i;
  float ff = clamp(f*1.7 - aR.x*0.7, 0.0, 1.0);
  ff = ff*ff*(3.0-2.0*ff);
  vec3 a = pick(i); vec3 b = pick(i+1.0);
  vec3 p = mix(a, b, ff);
  float tr = sin(3.14159*ff);
  p += vec3(sin(a.y*2.0+uTime+aR.y*6.0), cos(a.z*2.0+uTime*1.1), sin(a.x*2.0+uTime*0.9+aR.z*6.0))*tr*0.9;
  p += normalize(p+vec3(0.0001))*sin(uTime*0.8+aR.y*6.28)*0.05*(1.0+uAmp*2.0);
  p += vec3(sin(p.y*3.0+uTime*2.0), sin(p.z*3.0+uTime*2.3), sin(p.x*3.0+uTime*1.9))*0.07*uAmp;
  p += normalize(p+vec3(0.0001))*sin(length(p)*4.0-uTime*5.0)*uPulse*0.14;
  vec3 sc = normalize(aR.xyz-0.5+vec3(0.0001))*(5.0+aR.w*7.0);
  float ik = clamp(uIntro*1.6 - aR.y*0.6, 0.0, 1.0);
  ik = 1.0 - pow(1.0-ik, 3.0);
  p = mix(sc, p, ik);
  float c = cos(uRot), s = sin(uRot);
  p = vec3(c*p.x + s*p.z, p.y, -s*p.x + c*p.z);
  p = p*uScale + uOffset;
  vec2 d = p.xy - uMouse.xy;
  float dist = length(d);
  float push = smoothstep(1.7, 0.0, dist)*uMouseStr;
  p.xy += normalize(d+vec2(0.0001))*push*0.6;
  p.z += push*0.6;
  vec4 mv = modelViewMatrix*vec4(p,1.0);
  gl_Position = projectionMatrix*mv;
  gl_PointSize = min((1.7 + aR.w*2.2)*uPx*(7.0/-mv.z)*(1.0+push*1.4), 7.0*uPx);
  vC = mix(uColA, uColB, smoothstep(-2.4, 2.4, p.y + (aR.z-0.5)*1.4));
  vA = uOpacity*(0.6+0.8*aR.w)*(0.65+0.5*smoothstep(-3.0,3.0,p.z))*(1.0+push*1.2);
}`;
const FS = `
precision mediump float;
varying vec3 vC; varying float vA;
void main(){
  float d = length(gl_PointCoord-0.5);
  if(d>0.5) discard;
  float a = pow(smoothstep(0.5,0.0,d),1.6);
  gl_FragColor = vec4(vC*1.15, a*vA);
}`;

function initGL() {
  const canvas = $("#gl");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true, powerPreference: "high-performance" });
  const DPR = Math.min(devicePixelRatio || 1, 1.6);
  renderer.setPixelRatio(DPR);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  const N = innerWidth < 820 ? 16000 : 42000;

  const P = [0, 1, 2, 3].map(() => new Float32Array(N * 3));
  const R = new Float32Array(N * 4);
  const rnd = Math.random, g = () => (rnd() + rnd() + rnd() - 1.5);
  const rotX = (v, a) => { const c = Math.cos(a), s = Math.sin(a); return [v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c]; };
  const put = (k, i, v) => { P[k][i * 3] = v[0]; P[k][i * 3 + 1] = v[1]; P[k][i * 3 + 2] = v[2]; };
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2, rad = Math.sqrt(1 - y * y), phi = i * 2.399963, r0 = 2.35 * (0.95 + rnd() * 0.08);
    put(0, i, [Math.cos(phi) * rad * r0, y * r0, Math.sin(phi) * rad * r0]);
    const wx = (rnd() * 2 - 1) * 4.6, wz = (rnd() * 2 - 1) * 3.4;
    put(1, i, rotX([wx, Math.sin(wx * 1.2) * Math.cos(wz * 1.4) * 0.75 + Math.sin(wx * 3 + wz * 2) * 0.12, wz], -0.5));
    const t = rnd() * Math.PI * 2, kr = Math.cos(3 * t) + 2;
    put(2, i, [kr * Math.cos(2 * t) * 0.72 + g() * 0.11, kr * Math.sin(2 * t) * 0.72 + g() * 0.11, -Math.sin(3 * t) * 0.72 + g() * 0.11]);
    if (rnd() < 0.22) put(3, i, rotX([g() * 0.9, g() * 0.55, g() * 0.9], 0.8));
    else {
      const rr = Math.pow(rnd(), 0.55) * 3.3, ang = rr * 1.25 + (i % 3) * 2.0944 + g() * (0.16 + 0.07 * rr);
      put(3, i, rotX([Math.cos(ang) * rr, g() * 0.22 * (1 - rr / 5), Math.sin(ang) * rr], 0.8));
    }
    R[i * 4] = rnd(); R[i * 4 + 1] = rnd(); R[i * 4 + 2] = rnd(); R[i * 4 + 3] = rnd();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(P[0], 3));
  ["aP0", "aP1", "aP2", "aP3"].forEach((n, k) => geo.setAttribute(n, new THREE.BufferAttribute(P[k], 3)));
  geo.setAttribute("aR", new THREE.BufferAttribute(R, 4));

  const U = {
    uTime: { value: 0 }, uMorph: { value: 0 }, uIntro: { value: 0 }, uPx: { value: DPR }, uRot: { value: 0 },
    uAmp: { value: 0 }, uPulse: { value: 0 }, uScale: { value: 1 }, uOpacity: { value: 1 }, uMouseStr: { value: 0 },
    uMouse: { value: new THREE.Vector3(99, 99, 0) }, uOffset: { value: new THREE.Vector3() },
    uColA: { value: new THREE.Color("#8ea2ff") }, uColB: { value: new THREE.Color("#ffc7a0") }
  };
  const mat = new THREE.ShaderMaterial({ uniforms: U, vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  scene.add(pts);

  const resize = () => {
    renderer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.position.z = innerWidth < 820 ? 9.2 : 7.2;
    U.uPx.value = DPR * (innerWidth < 820 ? 0.75 : 1);
    camera.updateProjectionMatrix();
  };
  resize(); addEventListener("resize", resize);

  let mx = 0, my = 0, smx = 0, smy = 0, moved = -99;
  addEventListener("pointermove", (e) => { mx = (e.clientX / innerWidth) * 2 - 1; my = (e.clientY / innerHeight) * 2 - 1; moved = performance.now(); });

  return (time, dt) => {
    const mob = innerWidth < 820;
    S.think += (S.thinkT - S.think) * 0.06;
    S.pulse *= 0.93;
    S.spin += dt * S.think * 1.4;
    smx += (mx - smx) * 0.06; smy += (my - smy) * 0.06;
    const halfH = Math.tan((45 / 2) * Math.PI / 180) * camera.position.z;
    const auto = !fine || performance.now() - moved > 2500;
    const tx = auto ? Math.sin(time * 0.5) * 1.8 : smx * halfH * camera.aspect;
    const ty = auto ? Math.cos(time * 0.7) * 1.2 : -smy * halfH;
    U.uMouse.value.x += (tx - U.uMouse.value.x) * 0.12; U.uMouse.value.y += (ty - U.uMouse.value.y) * 0.12;
    U.uMouseStr.value += ((auto ? 0.35 : 1) - U.uMouseStr.value) * 0.05;
    U.uTime.value = reduce ? 0 : time;
    U.uMorph.value = S.morph; U.uIntro.value = S.intro;
    U.uAmp.value = S.think; U.uPulse.value = S.pulse;
    U.uScale.value = S.scale * (mob ? 0.82 : 1);
    U.uOpacity.value = S.opacity * (mob ? 0.7 : 1);
    U.uRot.value = S.rot + S.spin + smx * 0.25;
    U.uOffset.value.set(0, mob ? 1.1 : 0.1, 0);
    camera.position.x += (smx * 0.35 - camera.position.x) * 0.04;
    camera.position.y += (-smy * 0.2 - camera.position.y) * 0.04;
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  };
}
let gl = null;
try { if (window.THREE) gl = initGL(); else root.classList.add("no-gl"); } catch (err) { console.warn("WebGL unavailable", err); root.classList.add("no-gl"); }

/* ---------- scroll choreography ---------- */
const nav = $("#nav"), prog = $("#prog"), story = $("#story"), chaps = $$(".chap"), rails = $$(".rail span"), sIdx = $("#sIdx"), sbar = $("#sbar");
const hs = $("#usecases"), hrow = $("#hrow"), hbar = $("#hbar"), cta = $("#cta");
let curChap = -1;
const vis = (el) => {
  const r = el.getBoundingClientRect(), vh = innerHeight;
  return Math.min(clamp((vh - r.top) / (vh * 0.5)), clamp(r.bottom / (vh * 0.5)));
};
function scrollState(y, vh) {
  const hero = clamp(1 - y / (vh * 0.9));
  const sr = story.getBoundingClientRect();
  const sp = clamp(-sr.top / (story.offsetHeight - vh));
  const t = sp * 4, c = Math.min(3, Math.floor(t)), f = t - c;
  let morph = c;
  if (c > 0 && f < 0.28) morph = c - 1 + smooth(f / 0.28);
  if (sr.top > 0) morph = 0;
  const cr = cta.getBoundingClientRect();
  const cp = clamp((vh - cr.top) / (vh * 0.95));
  if (sr.bottom < vh * 1.2) morph = Math.min(morph, 3) * (1 - smooth(cp));
  S.morph = morph;
  S.scale = lerp(1, 1.04, vis(story));
  S.rot = Math.sin(performance.now() * 0.0004) * 0.4 + sp * 0.35;
  S.opacity = Math.max(hero, vis(story), vis(cta) * 0.95, 0.1);
  const idx = sr.top > 0 ? 0 : Math.min(3, Math.floor(clamp(sp * 4, 0, 3.999)));
  if (idx !== curChap) {
    curChap = idx;
    chaps.forEach((el, i) => el.classList.toggle("on", i === idx));
    rails.forEach((el, i) => el.classList.toggle("on", i === idx));
    sIdx.textContent = "0" + (idx + 1);
  }
  sbar.style.transform = "scaleX(" + sp + ")";
  const hr = hs.getBoundingClientRect(), hp = clamp(-hr.top / (hs.offsetHeight - vh));
  const dist = Math.max(0, hrow.scrollWidth - innerWidth);
  hrow.style.transform = "translate3d(" + (-hp * dist).toFixed(1) + "px,0,0)";
  hbar.style.transform = "scaleX(" + hp + ")";
}

/* ---------- main loop ---------- */
let prev = performance.now();
function tick(now) {
  const dt = Math.min(0.05, (now - prev) / 1000); prev = now;
  if (lenis) lenis.raf(now);
  const y = scrollY, vh = innerHeight;
  nav.classList.toggle("scrolled", y > 40);
  const h = root.scrollHeight - vh;
  prog.style.transform = "scaleX(" + (h > 0 ? y / h : 0) + ")";
  scrollState(y, vh);
  if (gl) gl(now / 1000, dt);
  requestAnimationFrame(tick);
}

/* ---------- loader + intro ---------- */
const loader = $("#loader"), lc = $("#lc"), lb = $("#lb");
let loaded = document.readyState === "complete", lp = 0, started = false;
addEventListener("load", () => { loaded = true; });
const t0 = performance.now(), minT = reduce ? 0 : 1600;
function finishLoad() {
  if (started) return; started = true;
  lc.textContent = "100%"; lb.style.transform = "scaleX(1)";
  loader.classList.add("done"); root.classList.add("ready");
  if (!reduce) { const s = performance.now(); const go = (n) => { const k = clamp((n - s) / 2800); S.intro = 1 - Math.pow(1 - k, 3); if (k < 1) requestAnimationFrame(go); }; setTimeout(() => requestAnimationFrame(go), 250); }
  setTimeout(() => { loader.style.visibility = "hidden"; }, 1300);
}
(function loadTick() {
  const el = performance.now() - t0;
  const target = loaded ? 100 : Math.min(86, el / 18);
  lp += (target - lp) * 0.09;
  lc.textContent = Math.round(lp) + "%"; lb.style.transform = "scaleX(" + lp / 100 + ")";
  if ((loaded && el > minT && lp > 98.5) || el > 5500) finishLoad(); else requestAnimationFrame(loadTick);
})();
requestAnimationFrame(tick);

/* ---------- cursor, tilt ---------- */
if (fine) {
  const dot = $(".cur-dot"), ring = $(".cur-ring");
  let x = innerWidth / 2, y = innerHeight / 2, rx = x, ry = y;
  addEventListener("mousemove", (e) => { x = e.clientX; y = e.clientY; dot.style.transform = "translate(" + x + "px," + y + "px)"; });
  (function loop() { rx += (x - rx) * 0.18; ry += (y - ry) * 0.18; ring.style.transform = "translate(" + rx + "px," + ry + "px)"; requestAnimationFrame(loop); })();
  document.addEventListener("mouseover", (e) => ring.classList.toggle("big", !!e.target.closest("a,button,summary,.chip,.tilt")));
  document.body.classList.add("has-cursor");
  $$(".tilt").forEach((c) => {
    c.addEventListener("mousemove", (e) => {
      const r = c.getBoundingClientRect(), px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
      c.style.setProperty("--mx", px * 100 + "%"); c.style.setProperty("--my", py * 100 + "%");
      if (!reduce && c.classList.contains("in")) c.style.transform = "perspective(1000px) rotateX(" + ((0.5 - py) * 5) + "deg) rotateY(" + ((px - 0.5) * 7) + "deg)";
    });
    c.addEventListener("mouseleave", () => { c.style.transform = ""; });
  });
}

/* ---------- chatbot ---------- */
const chat = $("#chat"), msgs = $("#msgs"), form = $("#chatForm"), input = $("#chatInput"), sendBtn = $("#sendBtn"), launcher = $("#launcher"), chips = $("#chips");
let history = [], busy = false;

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const md = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`(.+?)`/g, "<code>$1</code>").replace(/^[-*] /gm, "\u2022 ").replace(/\n/g, "<br>");
const toBottom = () => { msgs.scrollTop = msgs.scrollHeight; };
function bubble(role, html) {
  const row = document.createElement("div");
  row.className = "msg " + role;
  row.innerHTML = (role === "bot" ? '<span class="av"></span>' : "") + '<div class="bub">' + html + "</div>";
  msgs.appendChild(row); toBottom(); return row;
}
function greet() { bubble("bot", "Hi, I'm <strong>Lumen</strong>. Ask me anything, or pick a suggestion below."); }
function reveal(el, text) {
  return new Promise((done) => {
    const parts = text.split(/(\s+)/); let i = 0, acc = "";
    const step = () => {
      acc += parts[i++] || ""; el.innerHTML = md(acc); toBottom();
      if (i % 2 === 0) orbKick(0.3);
      if (i < parts.length) setTimeout(step, reduce ? 0 : 22 + Math.random() * 28); else done();
    };
    step();
  });
}
function openChat() {
  chat.classList.add("open"); chat.setAttribute("aria-hidden", "false"); document.body.classList.add("chat-open");
  if (!msgs.children.length) greet();
  setTimeout(() => input.focus(), 350);
}
function closeChat() {
  chat.classList.remove("open"); chat.setAttribute("aria-hidden", "true"); document.body.classList.remove("chat-open"); launcher.focus({ preventScroll: true });
}
function newChat() { history = []; msgs.innerHTML = ""; chips.style.display = ""; greet(); input.focus(); }
const syncSend = () => { sendBtn.disabled = busy || !input.value.trim(); };

async function send(text) {
  text = (text || "").trim();
  if (busy || !text) return;
  openChat();
  busy = true; syncSend(); chips.style.display = "none";
  bubble("user", md(text)); history.push({ role: "user", content: text });
  input.value = ""; input.style.height = "auto";
  const typing = bubble("bot", '<span class="typing"><i></i><i></i><i></i></span>');
  orbSet("thinking");
  let reply = "Sorry, something went wrong. Please try again.";
  try {
    const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ messages: history.slice(-12) }) });
    const data = await res.json();
    if (data.reply) reply = data.reply;
    if (data.mode === "demo") $("#mode span").textContent = "Demo mode";
  } catch (err) { console.warn(err); }
  orbSet("idle");
  await reveal($(".bub", typing), reply);
  history.push({ role: "assistant", content: reply });
  busy = false; syncSend(); input.focus();
}
$$("[data-open]").forEach((b) => b.addEventListener("click", openChat));
launcher.addEventListener("click", openChat);
$("#closeChat").addEventListener("click", closeChat);
$("#newChat").addEventListener("click", newChat);
addEventListener("keydown", (e) => {
  if (e.key === "Escape" && chat.classList.contains("open")) closeChat();
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); chat.classList.contains("open") ? closeChat() : openChat(); }
});
input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 120) + "px"; syncSend(); orbKick(0.12); });
input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
[["#heroForm", "#heroInput"], ["#ctaForm", "#ctaInput"]].forEach(([f, i]) => {
  const fe = $(f), ie = $(i);
  fe.addEventListener("submit", (e) => { e.preventDefault(); const v = ie.value; ie.value = ""; v.trim() ? send(v) : openChat(); });
  ie.addEventListener("input", () => orbKick(0.12));
});
$$(".chip").forEach((c) => c.addEventListener("click", () => send(c.textContent)));

window.__ok = true;
})();
</script>
</body>
</html>
'''


if __name__ == "__main__":
    app.run(debug=True)
