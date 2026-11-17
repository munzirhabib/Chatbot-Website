"""
Lumen - AI chatbot website (single file)
Language : Python (backend), HTML/CSS/JavaScript (frontend)
Framework: Flask (serves the page and the /api/chat endpoint)
3D       : Three.js (WebGL orb + particles), animation: GSAP + ScrollTrigger, smooth scroll: Lenis
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
<meta name="theme-color" content="#05060a">
<title>Lumen | The AI assistant that feels alive</title>
<meta name="description" content="Lumen is an AI chatbot with a living 3D interface. Ask anything and watch it respond.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%237c5cff'/%3E%3Ccircle cx='12' cy='12' r='5' fill='%2300e5ff'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#05060a;--fg:#eef1ff;--muted:#8d95b8;--a:#7c5cff;--b:#00e5ff;--c:#ff4fd8;--line:rgba(255,255,255,.09);--glass:rgba(255,255,255,.045)}
*{box-sizing:border-box;margin:0}
html{background:var(--bg);scroll-behavior:smooth}
html.lenis,html.lenis body{height:auto}
.lenis.lenis-smooth{scroll-behavior:auto!important}
body{font-family:Inter,system-ui,sans-serif;color:var(--fg);background:var(--bg);line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}
h1,h2,h3,.disp{font-family:"Space Grotesk",Inter,sans-serif;letter-spacing:-.02em;line-height:1.05}
a{color:inherit;text-decoration:none}
button{font:inherit;color:inherit;cursor:pointer}
:focus-visible{outline:2px solid var(--b);outline-offset:3px;border-radius:8px}
.i{width:1.25em;height:1.25em;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.aurora{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(60vw 50vh at 85% 10%,rgba(124,92,255,.22),transparent 60%),radial-gradient(50vw 50vh at 5% 70%,rgba(0,229,255,.12),transparent 60%),radial-gradient(40vw 40vh at 60% 100%,rgba(255,79,216,.12),transparent 60%)}
#gl{position:fixed;inset:0;width:100%;height:100%;z-index:1;pointer-events:none;transition:opacity .4s}
#fallbackOrb{display:none;position:fixed;right:8vw;top:22vh;width:min(46vw,460px);aspect-ratio:1;border-radius:50%;z-index:1;background:radial-gradient(circle at 35% 30%,var(--b),var(--a) 55%,var(--c));filter:blur(2px);opacity:.85;animation:float 7s ease-in-out infinite}
.no-gl #fallbackOrb{display:block}
main,footer{position:relative;z-index:2}
#prog{position:fixed;top:0;left:0;height:2px;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,var(--a),var(--b),var(--c));z-index:100}
.wrap{width:min(1180px,90vw);margin:auto}
section{padding:clamp(70px,12vh,140px) 0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:.78rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--b);margin-bottom:18px}
.eyebrow::before{content:"";width:22px;height:1px;background:var(--b)}
h2{font-size:clamp(2rem,4.6vw,3.6rem);font-weight:700;max-width:18ch}
.sub{color:var(--muted);font-size:1.1rem;max-width:52ch;margin-top:16px}
.grad{background:linear-gradient(100deg,var(--b),var(--a) 50%,var(--c));-webkit-background-clip:text;background-clip:text;color:transparent}

/* nav */
.nav{position:fixed;top:16px;left:0;right:0;display:flex;justify-content:center;z-index:50;pointer-events:none}
.pill{pointer-events:auto;display:flex;align-items:center;gap:30px;padding:9px 10px 9px 22px;border:1px solid var(--line);background:rgba(10,12,20,.55);backdrop-filter:blur(16px) saturate(1.4);border-radius:999px}
.logo{display:flex;align-items:center;gap:10px;font-family:"Space Grotesk",sans-serif;font-weight:700;font-size:1.15rem}
.dot{width:18px;height:18px;border-radius:50%;background:radial-gradient(circle at 30% 30%,var(--b),var(--a) 60%,var(--c))}
.links{display:flex;gap:24px;color:var(--muted);font-size:.95rem}
.links a{transition:color .2s}.links a:hover{color:#fff}
@media(max-width:820px){.links{display:none}.pill{gap:16px}}

/* buttons */
.btn{display:inline-flex;align-items:center;gap:10px;padding:14px 26px;border-radius:999px;font-weight:600;border:1px solid var(--line);background:var(--glass);transition:transform .3s,background .3s,box-shadow .3s}
.btn:hover{transform:translateY(-2px);background:rgba(255,255,255,.09)}
.btn.primary{background:linear-gradient(120deg,var(--a),var(--b));color:#04050a;border:0;box-shadow:0 10px 40px -12px var(--a)}
.btn.primary:hover{box-shadow:0 16px 50px -10px var(--b)}
.btn.sm{padding:10px 18px;font-size:.92rem}
.row{display:flex;gap:14px;flex-wrap:wrap}

/* hero */
.hero{position:relative;min-height:100svh;display:flex;align-items:center;padding-top:110px;padding-bottom:60px}
.hero .wrap{display:grid;grid-template-columns:1.05fr .95fr;gap:30px;align-items:center}
.badge{display:inline-flex;align-items:center;gap:10px;padding:7px 14px;border:1px solid var(--line);border-radius:999px;background:var(--glass);font-size:.85rem;color:var(--muted);margin-bottom:26px}
.badge b{color:var(--fg);font-weight:600}
.badge i{width:7px;height:7px;border-radius:50%;background:#2dff9a;box-shadow:0 0 12px #2dff9a}
.hero h1{font-size:clamp(2.9rem,7.4vw,6.4rem);font-weight:700;max-width:11ch}
.w{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.1em}
.w>span{display:inline-block}
.js:not(.reduce) .hero h1 .w>span{transform:translateY(112%)}
.hero p.sub{margin:26px 0 34px}
.trust{display:flex;gap:22px;flex-wrap:wrap;margin-top:34px;color:var(--muted);font-size:.9rem}
.trust span{display:flex;align-items:center;gap:8px}.trust .i{color:var(--b)}
.hero-art{position:relative;height:min(60vh,520px)}
.fcard{position:absolute;display:flex;gap:12px;align-items:center;padding:13px 18px;border-radius:16px;border:1px solid var(--line);background:rgba(10,12,22,.6);backdrop-filter:blur(14px);font-size:.9rem;animation:float 6s ease-in-out infinite}
.fcard b{display:block;font-size:1.1rem}
.fcard small{color:var(--muted)}
.fcard .i{color:var(--b);width:1.6em;height:1.6em}
.f1{top:6%;right:0}.f2{bottom:8%;left:0;animation-delay:-3s}
@keyframes float{50%{transform:translateY(-14px)}}
.scrollcue{position:absolute;left:50%;bottom:22px;width:24px;height:38px;border:1.5px solid var(--line);border-radius:14px;transform:translateX(-50%)}
.scrollcue::after{content:"";position:absolute;left:50%;top:7px;width:3px;height:7px;margin-left:-1.5px;border-radius:2px;background:var(--b);animation:cue 1.8s infinite}
@keyframes cue{0%{opacity:1;transform:translateY(0)}100%{opacity:0;transform:translateY(14px)}}
@media(max-width:820px){.hero .wrap{grid-template-columns:1fr}.hero-art{display:none}.hero{padding-top:44vh;align-items:flex-end}.scrollcue{display:none}}

/* marquee */
.marq{overflow:hidden;border-block:1px solid var(--line);padding:24px 0;background:rgba(5,6,10,.55);backdrop-filter:blur(6px);-webkit-mask-image:linear-gradient(90deg,transparent,#000 12%,#000 88%,transparent);mask-image:linear-gradient(90deg,transparent,#000 12%,#000 88%,transparent)}
.track{display:flex;gap:70px;width:max-content;animation:marq 34s linear infinite;font-family:"Space Grotesk",sans-serif;font-size:1.35rem;font-weight:700;color:#5d6488;letter-spacing:.02em}
@keyframes marq{to{transform:translateX(-50%)}}

/* bento */
.veil{background:linear-gradient(180deg,rgba(5,6,10,.0),rgba(5,6,10,.6) 18%,rgba(5,6,10,.6) 82%,rgba(5,6,10,0))}
.bento{display:grid;grid-template-columns:repeat(6,1fr);gap:18px;margin-top:54px}
.card{position:relative;padding:30px;border-radius:26px;border:1px solid var(--line);background:var(--glass);backdrop-filter:blur(10px);overflow:hidden;transition:transform .25s ease,border-color .3s;will-change:transform}
.card::before{content:"";position:absolute;inset:0;background:radial-gradient(520px circle at var(--mx,50%) var(--my,0%),rgba(124,92,255,.24),transparent 45%);opacity:0;transition:opacity .3s;pointer-events:none}
.card:hover{border-color:rgba(124,92,255,.5)}.card:hover::before{opacity:1}
.card .ic{width:48px;height:48px;border-radius:14px;display:grid;place-items:center;margin-bottom:22px;background:linear-gradient(135deg,rgba(124,92,255,.35),rgba(0,229,255,.2));color:#fff}
.card h3{font-size:1.45rem;margin-bottom:10px}
.card p{color:var(--muted)}
.s4{grid-column:span 4}.s2{grid-column:span 2}
.bars{display:flex;align-items:flex-end;gap:5px;height:90px;margin-top:26px}
.bars span{flex:1;border-radius:4px;background:linear-gradient(180deg,var(--b),var(--a));animation:bar 1.4s ease-in-out infinite;transform-origin:bottom}
@keyframes bar{0%,100%{transform:scaleY(.2)}50%{transform:scaleY(1)}}
@media(max-width:900px){.bento{grid-template-columns:1fr}.bento>.card{grid-column:auto!important}}

/* demo */
.split{display:grid;grid-template-columns:.9fr 1.1fr;gap:56px;align-items:center}
@media(max-width:900px){.split{grid-template-columns:1fr}}
.win{border-radius:24px;border:1px solid var(--line);background:rgba(10,12,22,.7);backdrop-filter:blur(18px);overflow:hidden;box-shadow:0 40px 100px -30px rgba(124,92,255,.45)}
.win-h{display:flex;gap:8px;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line);color:var(--muted);font-size:.85rem}
.win-h i{width:11px;height:11px;border-radius:50%;background:#2a2f45}
.win-b{padding:22px;display:flex;flex-direction:column;gap:14px;min-height:330px}
.dm{max-width:82%;padding:13px 17px;border-radius:18px;font-size:.96rem;opacity:0;transform:translateY(14px);transition:opacity .5s,transform .5s}
.dm.in{opacity:1;transform:none}
.dm.u{align-self:flex-end;background:linear-gradient(120deg,var(--a),#5b7cff);border-bottom-right-radius:5px}
.dm.b{align-self:flex-start;background:var(--glass);border:1px solid var(--line);border-bottom-left-radius:5px}

/* stats / steps */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;text-align:center}
.stat{padding:34px 10px;border-radius:24px;border:1px solid var(--line);background:var(--glass)}
.stat b{display:block;font-family:"Space Grotesk",sans-serif;font-size:clamp(2.2rem,4.4vw,3.6rem)}
.stat span{color:var(--muted)}
@media(max-width:820px){.stats{grid-template-columns:repeat(2,1fr)}}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:54px;counter-reset:s}
.step{counter-increment:s;padding:34px;border-radius:26px;border:1px solid var(--line);background:var(--glass)}
.step::before{content:"0" counter(s);display:block;font-family:"Space Grotesk",sans-serif;font-size:3.4rem;font-weight:700;margin-bottom:14px;background:linear-gradient(120deg,var(--b),var(--c));-webkit-background-clip:text;background-clip:text;color:transparent}
.step h3{font-size:1.4rem;margin-bottom:8px}.step p{color:var(--muted)}
@media(max-width:820px){.steps{grid-template-columns:1fr}}

/* faq */
.faq{max-width:820px;margin-top:44px;display:grid;gap:12px}
details{border:1px solid var(--line);border-radius:18px;background:var(--glass);padding:20px 24px;transition:border-color .3s}
details[open]{border-color:rgba(124,92,255,.5)}
summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;gap:20px;font-weight:600;font-size:1.05rem}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";font-size:1.5rem;line-height:1;color:var(--b);transition:transform .3s}
details[open] summary::after{transform:rotate(45deg)}
details p{color:var(--muted);margin-top:12px}

/* cta + footer */
.cta{border-radius:34px;padding:clamp(44px,8vw,96px) 24px;text-align:center;border:1px solid var(--line);background:radial-gradient(800px circle at 50% 0%,rgba(124,92,255,.38),transparent 60%),var(--glass);backdrop-filter:blur(10px)}
.cta h2{margin:0 auto 18px;max-width:16ch}.cta .sub{margin:0 auto 32px}.cta .row{justify-content:center}
footer{border-top:1px solid var(--line);padding:48px 0;color:var(--muted);background:rgba(5,6,10,.7)}
.fwrap{display:flex;justify-content:space-between;gap:30px;flex-wrap:wrap;align-items:center}
footer .links{display:flex}

/* cursor */
.cur-dot,.cur-ring{position:fixed;left:0;top:0;pointer-events:none;z-index:200;display:none}
.has-cursor .cur-dot,.has-cursor .cur-ring{display:block}
.cur-dot{width:7px;height:7px;margin:-3.5px 0 0 -3.5px;border-radius:50%;background:#fff;mix-blend-mode:difference}
.cur-ring{width:38px;height:38px;margin:-19px 0 0 -19px;border-radius:50%;border:1.5px solid rgba(255,255,255,.5);transition:width .25s,height .25s,margin .25s,background .25s}
.cur-ring.big{width:64px;height:64px;margin:-32px 0 0 -32px;background:rgba(124,92,255,.15)}
.has-cursor,.has-cursor a,.has-cursor button,.has-cursor summary{cursor:none}

/* chat */
#launcher{position:fixed;right:22px;bottom:22px;z-index:80;width:64px;height:64px;border-radius:50%;border:0;background:radial-gradient(circle at 30% 30%,var(--b),var(--a) 60%,var(--c));box-shadow:0 12px 40px -6px var(--a);display:grid;place-items:center;transition:transform .3s;color:#04050a}
#launcher:hover{transform:scale(1.08) rotate(-4deg)}
#launcher::after{content:"";position:absolute;inset:-6px;border-radius:50%;border:2px solid var(--a);animation:ping 2.4s infinite}
@keyframes ping{0%{transform:scale(.9);opacity:.7}100%{transform:scale(1.5);opacity:0}}
#launcher .i{width:28px;height:28px;stroke-width:2}
#chat{position:fixed;right:22px;bottom:100px;z-index:90;width:min(400px,calc(100vw - 24px));height:min(620px,calc(100svh - 130px));display:flex;flex-direction:column;border-radius:26px;border:1px solid rgba(255,255,255,.14);background:rgba(10,12,22,.8);backdrop-filter:blur(24px) saturate(1.5);box-shadow:0 40px 120px -20px rgba(0,0,0,.85),0 0 0 1px rgba(124,92,255,.15);transform-origin:bottom right;opacity:0;visibility:hidden;pointer-events:none;transform:translateY(20px) scale(.92);transition:opacity .35s,transform .45s cubic-bezier(.2,.9,.3,1.2),visibility .35s}
#chat.open{opacity:1;visibility:visible;pointer-events:auto;transform:none}
@media(max-width:560px){#chat{right:12px;left:12px;width:auto;bottom:92px}}
.ch{display:flex;align-items:center;gap:12px;padding:16px 18px;border-bottom:1px solid var(--line)}
.ch .dot{width:38px;height:38px;position:relative}
.ch .dot::after{content:"";position:absolute;right:0;bottom:0;width:11px;height:11px;border-radius:50%;background:#2dff9a;border:2px solid #0a0c16}
.ch b{display:block;font-family:"Space Grotesk",sans-serif;font-size:1.05rem}
.ch small{color:var(--muted);font-size:.78rem}
.ch .x{margin-left:auto;width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--glass);display:grid;place-items:center}
.ch .x:hover{background:rgba(255,255,255,.1)}
#msgs{flex:1;overflow-y:auto;padding:8px 18px;scroll-behavior:smooth;overscroll-behavior:contain}
#msgs::-webkit-scrollbar{width:6px}#msgs::-webkit-scrollbar-thumb{background:#2a2f45;border-radius:3px}
.msg{display:flex;gap:10px;margin:14px 0;animation:pop .35s ease}
@keyframes pop{from{opacity:0;transform:translateY(10px)}}
.msg .dot{width:26px;height:26px;margin-top:2px}
.bub{max-width:82%;padding:11px 15px;border-radius:18px;font-size:.95rem;line-height:1.55;word-wrap:break-word}
.msg.bot .bub{background:var(--glass);border:1px solid var(--line);border-top-left-radius:5px}
.msg.user{justify-content:flex-end}
.msg.user .bub{background:linear-gradient(120deg,var(--a),#5b7cff);border-bottom-right-radius:5px}
.bub code{background:rgba(255,255,255,.1);padding:1px 6px;border-radius:5px;font-size:.88em}
.typing{display:flex;gap:5px;padding:14px 16px}
.typing i{width:7px;height:7px;border-radius:50%;background:var(--muted);animation:dots 1.2s infinite}
.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes dots{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
.chips{display:flex;flex-wrap:wrap;gap:8px;padding:6px 18px 12px}
.chip{padding:8px 14px;border-radius:999px;border:1px solid var(--line);background:var(--glass);font-size:.85rem;transition:background .2s,border-color .2s,transform .2s}
.chip:hover{background:rgba(124,92,255,.22);border-color:var(--a);transform:translateY(-2px)}
#chatForm{display:flex;gap:10px;padding:14px 16px 16px;border-top:1px solid var(--line)}
#chatInput{flex:1;min-width:0;padding:13px 18px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.05);color:var(--fg);font:inherit;font-size:.95rem}
#chatInput::placeholder{color:#6b7396}
#chatInput:focus{outline:none;border-color:var(--a);box-shadow:0 0 0 3px rgba(124,92,255,.25)}
#sendBtn{width:46px;height:46px;border-radius:50%;border:0;background:linear-gradient(120deg,var(--a),var(--b));display:grid;place-items:center;color:#04050a;transition:transform .2s,opacity .2s}
#sendBtn:hover{transform:scale(1.08)}#sendBtn:disabled{opacity:.4;transform:none;cursor:not-allowed}

/* reveal (only hidden when JS + GSAP are ready) */
.js:not(.reduce) [data-reveal]{opacity:0;transform:translateY(34px)}
.reduce *{animation:none!important;scroll-behavior:auto!important}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="i-bolt" viewBox="0 0 24 24"><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/></symbol>
  <symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></symbol>
  <symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M8.5 12l2.5 2.5L16 9.5"/></symbol>
  <symbol id="i-cpu" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></symbol>
  <symbol id="i-layers" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5"/></symbol>
  <symbol id="i-sliders" viewBox="0 0 24 24"><path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/></symbol>
  <symbol id="i-send" viewBox="0 0 24 24"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></symbol>
  <symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
  <symbol id="i-chat" viewBox="0 0 24 24"><path d="M21 12a8 8 0 01-11.6 7.1L4 20l1.1-4.6A8 8 0 1121 12z"/></symbol>
  <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
  <symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12l4.5 4.5L19 7"/></symbol>
</svg>

<div id="prog"></div>
<div class="cur-dot"></div><div class="cur-ring"></div>
<div class="aurora"></div>
<canvas id="gl" aria-hidden="true"></canvas>
<div id="fallbackOrb" aria-hidden="true"></div>

<header class="nav">
  <div class="pill" id="pill">
    <a class="logo" href="#top"><span class="dot"></span>Lumen</a>
    <nav class="links" aria-label="Main">
      <a href="#features">Features</a><a href="#demo">Demo</a><a href="#how">How it works</a><a href="#faq">FAQ</a>
    </nav>
    <button class="btn primary sm magnetic" data-open-chat>Try Lumen</button>
  </div>
</header>

<main id="top">
  <section class="hero">
    <div class="wrap">
      <div>
        <div class="badge" data-hero><i></i><span><b>Lumen 2.0</b> is live. Meet the AI that feels alive.</span></div>
        <h1 aria-label="The assistant that thinks with you.">
          <span class="w"><span>The</span></span>
          <span class="w"><span>assistant</span></span>
          <span class="w"><span>that</span></span>
          <span class="w"><span>thinks</span></span>
          <span class="w"><span class="grad">with&nbsp;you.</span></span>
        </h1>
        <p class="sub" data-hero>Ask anything, in any language. Lumen answers in seconds, and its 3D core reacts to every thought. Click the orb's chat button and feel the difference.</p>
        <div class="row" data-hero>
          <button class="btn primary magnetic" data-open-chat>Talk to Lumen <svg class="i"><use href="#i-arrow"/></svg></button>
          <a class="btn magnetic" href="#demo">See it in action</a>
        </div>
        <div class="trust" data-hero>
          <span><svg class="i"><use href="#i-check"/></svg>No sign-up needed</span>
          <span><svg class="i"><use href="#i-check"/></svg>Private by design</span>
          <span><svg class="i"><use href="#i-check"/></svg>95+ languages</span>
        </div>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="fcard f1"><svg class="i"><use href="#i-bolt"/></svg><div><b>0.8s</b><small>average response</small></div></div>
        <div class="fcard f2"><svg class="i"><use href="#i-globe"/></svg><div><b>95+</b><small>languages understood</small></div></div>
      </div>
    </div>
    <div class="scrollcue" aria-hidden="true"></div>
  </section>

  <div class="marq" aria-label="Trusted by">
    <div class="track">
      <span>NORTHWIND</span><span>Acme&nbsp;Labs</span><span>VERTEX</span><span>Helix</span><span>Paperplane</span><span>QUANTA</span><span>Brightly</span><span>ORBITAL</span>
      <span>NORTHWIND</span><span>Acme&nbsp;Labs</span><span>VERTEX</span><span>Helix</span><span>Paperplane</span><span>QUANTA</span><span>Brightly</span><span>ORBITAL</span>
    </div>
  </div>

  <section id="features" class="veil">
    <div class="wrap">
      <div data-reveal><span class="eyebrow">Features</span>
      <h2>Built to feel <span class="grad">effortless.</span></h2>
      <p class="sub">Every detail is designed so that talking to AI feels natural, fast and a little bit magical.</p></div>
      <div class="bento" data-reveal>
        <article class="card tilt s4">
          <div class="ic"><svg class="i"><use href="#i-bolt"/></svg></div>
          <h3>Instant, streaming answers</h3>
          <p>Replies appear word by word while the 3D core pulses with every thought, so you always know what Lumen is doing.</p>
          <div class="bars" aria-hidden="true"></div>
        </article>
        <article class="card tilt s2">
          <div class="ic"><svg class="i"><use href="#i-globe"/></svg></div>
          <h3>Speaks your language</h3>
          <p>Write in English, Urdu, Arabic or Spanish. Lumen replies in the same language.</p>
        </article>
        <article class="card tilt s2">
          <div class="ic"><svg class="i"><use href="#i-shield"/></svg></div>
          <h3>Private by design</h3>
          <p>Your conversations are never sold or used for ads.</p>
        </article>
        <article class="card tilt s2">
          <div class="ic"><svg class="i"><use href="#i-cpu"/></svg></div>
          <h3>Powered by Claude</h3>
          <p>A top-tier language model gives clear, careful and useful answers.</p>
        </article>
        <article class="card tilt s2">
          <div class="ic"><svg class="i"><use href="#i-sliders"/></svg></div>
          <h3>Fully customisable</h3>
          <p>Set the tone, name and knowledge so the bot sounds like your brand.</p>
        </article>
      </div>
    </div>
  </section>

  <section id="demo">
    <div class="wrap split">
      <div data-reveal>
        <span class="eyebrow">Live demo</span>
        <h2>Conversations that <span class="grad">flow.</span></h2>
        <p class="sub">Summaries, translations, ideas, code. Ask a question and keep going, Lumen remembers the thread.</p>
        <div class="row" style="margin-top:30px"><button class="btn primary magnetic" data-open-chat>Try it yourself <svg class="i"><use href="#i-arrow"/></svg></button></div>
      </div>
      <div class="win" data-reveal id="demoWin">
        <div class="win-h"><i></i><i></i><i></i><span style="margin-left:10px">Lumen &middot; online</span></div>
        <div class="win-b">
          <div class="dm u">Can you turn my meeting notes into 3 bullet points?</div>
          <div class="dm b">Of course. Paste them here and I will give you 3 crisp bullets, plus a list of action items.</div>
          <div class="dm u">Also translate it into Urdu.</div>
          <div class="dm b">Done. I can answer in 95+ languages, including Urdu, and keep the same tone.</div>
        </div>
      </div>
    </div>
  </section>

  <section class="veil">
    <div class="wrap">
      <div class="stats" data-reveal>
        <div class="stat"><b data-count="2" data-suffix="M+">2M+</b><span>Conversations</span></div>
        <div class="stat"><b data-count="95" data-suffix="+">95+</b><span>Languages</span></div>
        <div class="stat"><b data-count="99" data-suffix="%">99%</b><span>Uptime</span></div>
        <div class="stat"><b data-count="4" data-suffix=".9">4.9</b><span>User rating</span></div>
      </div>
    </div>
  </section>

  <section id="how">
    <div class="wrap">
      <div data-reveal><span class="eyebrow">How it works</span><h2>Three steps. <span class="grad">Zero friction.</span></h2></div>
      <div class="steps" data-reveal>
        <div class="step"><h3>Open the chat</h3><p>Click the glowing button. No account, no setup.</p></div>
        <div class="step"><h3>Ask anything</h3><p>Type a question or tap a suggestion to start.</p></div>
        <div class="step"><h3>Get real answers</h3><p>Clear replies in seconds, in your own language.</p></div>
      </div>
    </div>
  </section>

  <section id="faq" class="veil">
    <div class="wrap">
      <div data-reveal><span class="eyebrow">FAQ</span><h2>Questions, <span class="grad">answered.</span></h2></div>
      <div class="faq" data-reveal>
        <details><summary>Is Lumen free to try?</summary><p>Yes. Open the chat and start talking, no account needed.</p></details>
        <details><summary>Which languages does it support?</summary><p>More than 95, including English, Urdu, Arabic and Spanish.</p></details>
        <details><summary>Is my data safe?</summary><p>Conversations are private and never used for advertising.</p></details>
        <details><summary>Can I add it to my own website?</summary><p>Yes. Lumen is a single chat widget that can be dropped into any site.</p></details>
      </div>
    </div>
  </section>

  <section>
    <div class="wrap">
      <div class="cta" data-reveal>
        <h2>Ready to meet <span class="grad">Lumen?</span></h2>
        <p class="sub">Start a conversation in under five seconds.</p>
        <div class="row"><button class="btn primary magnetic" data-open-chat>Start chatting <svg class="i"><use href="#i-arrow"/></svg></button></div>
      </div>
    </div>
  </section>
</main>

<footer>
  <div class="wrap fwrap">
    <a class="logo" href="#top"><span class="dot"></span>Lumen</a>
    <nav class="links" aria-label="Footer"><a href="#features">Features</a><a href="#demo">Demo</a><a href="#faq">FAQ</a></nav>
    <small>&copy; 2026 Lumen. Demo project.</small>
  </div>
</footer>

<button id="launcher" aria-label="Open chat" aria-expanded="false" aria-controls="chat"><svg class="i"><use href="#i-chat"/></svg></button>

<section id="chat" role="dialog" aria-label="Chat with Lumen" aria-hidden="true">
  <div class="ch">
    <span class="dot"></span>
    <div><b>Lumen</b><small id="mode">Online &middot; replies in seconds</small></div>
    <button class="x" id="closeChat" aria-label="Close chat"><svg class="i"><use href="#i-close"/></svg></button>
  </div>
  <div id="msgs" aria-live="polite"></div>
  <div class="chips" id="chips">
    <button class="chip" type="button">What can you do?</button>
    <button class="chip" type="button">Explain AI in simple words</button>
    <button class="chip" type="button">Give me a business idea</button>
  </div>
  <form id="chatForm" autocomplete="off">
    <input id="chatInput" type="text" maxlength="500" placeholder="Ask Lumen anything..." aria-label="Your message" required>
    <button id="sendBtn" type="submit" aria-label="Send"><svg class="i"><use href="#i-send"/></svg></button>
  </form>
</section>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js"></script>
<script>
(() => {
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const root = document.documentElement;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const fine = matchMedia("(hover:hover) and (pointer:fine)").matches;
const hasGSAP = !!(window.gsap && window.ScrollTrigger);
if (reduce) root.classList.add("reduce");
if (hasGSAP) { gsap.registerPlugin(ScrollTrigger); root.classList.add("js"); }

/* ---------- smooth scroll ---------- */
let lenis = null;
if (window.Lenis && !reduce) {
  lenis = new Lenis({ lerp: 0.09 });
  if (hasGSAP) {
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((t) => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
  } else {
    const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }
}
$$('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
  const t = $(a.getAttribute("href"));
  if (!t) return;
  e.preventDefault();
  lenis ? lenis.scrollTo(t, { offset: -20 }) : t.scrollIntoView({ behavior: "smooth" });
}));

/* ---------- scroll progress ---------- */
const prog = $("#prog");
const onScroll = () => {
  const h = root.scrollHeight - innerHeight;
  prog.style.transform = "scaleX(" + (h > 0 ? scrollY / h : 0) + ")";
};
addEventListener("scroll", onScroll, { passive: true }); onScroll();

/* ---------- 3D orb (Three.js) ---------- */
let orbState = { amp: 1, spin: 0.15 }, orbTarget = { amp: 1, spin: 0.15 }, pulse = 0;
window.orbSet = (s) => {
  orbTarget = s === "thinking" ? { amp: 2.3, spin: 0.9 } : s === "speaking" ? { amp: 1.6, spin: 0.35 } : { amp: 1, spin: 0.15 };
};

const VS = `
uniform float uTime; uniform float uAmp;
varying vec3 vNormal; varying vec3 vView; varying float vN;
vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
float snoise(vec3 v){
  const vec2 C=vec2(1.0/6.0,1.0/3.0); const vec4 D=vec4(0.0,0.5,1.0,2.0);
  vec3 i=floor(v+dot(v,C.yyy)); vec3 x0=v-i+dot(i,C.xxx);
  vec3 g=step(x0.yzx,x0.xyz); vec3 l=1.0-g;
  vec3 i1=min(g.xyz,l.zxy); vec3 i2=max(g.xyz,l.zxy);
  vec3 x1=x0-i1+C.xxx; vec3 x2=x0-i2+C.yyy; vec3 x3=x0-D.yyy;
  i=mod289(i);
  vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
  float n_=0.142857142857; vec3 ns=n_*D.wyz-D.xzx;
  vec4 j=p-49.0*floor(p*ns.z*ns.z); vec4 x_=floor(j*ns.z); vec4 y_=floor(j-7.0*x_);
  vec4 x=x_*ns.x+ns.yyyy; vec4 y=y_*ns.x+ns.yyyy; vec4 h=1.0-abs(x)-abs(y);
  vec4 b0=vec4(x.xy,y.xy); vec4 b1=vec4(x.zw,y.zw);
  vec4 s0=floor(b0)*2.0+1.0; vec4 s1=floor(b1)*2.0+1.0; vec4 sh=-step(h,vec4(0.0));
  vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy; vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
  vec3 p0=vec3(a0.xy,h.x); vec3 p1=vec3(a0.zw,h.y); vec3 p2=vec3(a1.xy,h.z); vec3 p3=vec3(a1.zw,h.w);
  vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
  p0*=norm.x; p1*=norm.y; p2*=norm.z; p3*=norm.w;
  vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0); m=m*m;
  return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}
void main(){
  float n=snoise(normal*1.4+vec3(0.0,uTime*0.35,uTime*0.2));
  float n2=snoise(normal*3.2-vec3(uTime*0.5));
  float d=(n*0.24+n2*0.05)*uAmp;
  vec3 p=position+normal*d;
  vN=n;
  vNormal=normalize(normalMatrix*normal);
  vec4 mv=modelViewMatrix*vec4(p,1.0);
  vView=-mv.xyz;
  gl_Position=projectionMatrix*mv;
}`;
const FS = `
uniform vec3 uA; uniform vec3 uB; uniform vec3 uC;
varying vec3 vNormal; varying vec3 vView; varying float vN;
void main(){
  vec3 v=normalize(vView);
  float f=pow(1.0-max(dot(normalize(vNormal),v),0.0),2.2);
  vec3 col=mix(uA,uB,smoothstep(-0.6,0.8,vN));
  col=mix(col,uC,f*0.8);
  col+=f*0.9*uB;
  gl_FragColor=vec4(col*(0.45+0.65*f),0.94);
}`;

function initGL() {
  const canvas = $("#gl");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.z = 6;

  const uniforms = {
    uTime: { value: 0 }, uAmp: { value: 1 },
    uA: { value: new THREE.Color("#7c5cff") }, uB: { value: new THREE.Color("#00e5ff") }, uC: { value: new THREE.Color("#ff4fd8") }
  };
  const orb = new THREE.Mesh(new THREE.IcosahedronGeometry(1.5, 36), new THREE.ShaderMaterial({ uniforms, vertexShader: VS, fragmentShader: FS, transparent: true }));
  const wire = new THREE.Mesh(new THREE.IcosahedronGeometry(1.95, 3), new THREE.MeshBasicMaterial({ color: 0x7c5cff, wireframe: true, transparent: true, opacity: 0.12 }));
  const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.5, 0.006, 8, 180), new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.55 }));
  const ring2 = new THREE.Mesh(new THREE.TorusGeometry(2.95, 0.005, 8, 180), new THREE.MeshBasicMaterial({ color: 0xff4fd8, transparent: true, opacity: 0.35 }));
  const group = new THREE.Group();
  group.add(orb, wire, ring1, ring2);
  scene.add(group);

  const N = 1800, pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    const r = 4 + Math.random() * 10, th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1);
    pos[i * 3] = r * Math.sin(ph) * Math.cos(th);
    pos[i * 3 + 1] = r * Math.sin(ph) * Math.sin(th);
    pos[i * 3 + 2] = r * Math.cos(ph) - 2;
  }
  const pg = new THREE.BufferGeometry();
  pg.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const stars = new THREE.Points(pg, new THREE.PointsMaterial({ size: 0.03, color: 0xaab4ff, transparent: true, opacity: 0.75, depthWrite: false, blending: THREE.AdditiveBlending }));
  scene.add(stars);

  const resize = () => {
    renderer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  };
  resize(); addEventListener("resize", resize);

  let mx = 0, my = 0, smx = 0, smy = 0, ssy = scrollY;
  addEventListener("pointermove", (e) => { mx = (e.clientX / innerWidth) * 2 - 1; my = (e.clientY / innerHeight) * 2 - 1; });

  const clock = new THREE.Clock();
  const frame = () => {
    const t = clock.getElapsedTime();
    orbState.amp += (orbTarget.amp - orbState.amp) * 0.06;
    orbState.spin += (orbTarget.spin - orbState.spin) * 0.05;
    pulse *= 0.94;
    uniforms.uTime.value = t;
    uniforms.uAmp.value = orbState.amp + pulse;

    smx += (mx - smx) * 0.05; smy += (my - smy) * 0.05;
    ssy += (scrollY - ssy) * 0.08;
    const s = ssy / innerHeight, mob = innerWidth < 820;

    group.position.set(mob ? 0 : 2.1 * Math.cos(s * 1.5), (mob ? 1.7 : 0.1) - s * (mob ? 0.5 : 0.35), 0);
    group.rotation.y = t * orbState.spin + s * 1.2 + smx * 0.3;
    group.rotation.x = smy * 0.18 + s * 0.3;
    group.scale.setScalar((mob ? 0.78 : 1) - Math.min(s, 2) * 0.08);
    ring1.rotation.x = t * 0.2; ring1.rotation.y = t * 0.1;
    ring2.rotation.x = -t * 0.15; ring2.rotation.z = t * 0.12;
    wire.rotation.y = -t * 0.05;
    stars.rotation.y = t * 0.01 + s * 0.15; stars.position.y = s * 0.6;
    camera.position.x += (smx * 0.4 - camera.position.x) * 0.05;
    camera.position.y += (-smy * 0.25 - camera.position.y) * 0.05;
    camera.lookAt(0, 0, 0);
    canvas.style.opacity = Math.max(0.4, 1 - s * 0.45);
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  };
  frame();
  window.orbPulse = () => { pulse = Math.min(pulse + 0.5, 1.2); };
}
try { initGL(); } catch (err) { console.warn("WebGL unavailable", err); root.classList.add("no-gl"); }
window.orbPulse = window.orbPulse || (() => {});

/* ---------- GSAP animations ---------- */
if (hasGSAP && !reduce) {
  gsap.timeline({ defaults: { ease: "power4.out" } })
    .from("#pill", { y: -40, opacity: 0, duration: 1 })
    .to(".hero h1 .w > span", { y: 0, duration: 1.1, stagger: 0.07 }, 0.1)
    .from("[data-hero]", { y: 26, opacity: 0, duration: 0.9, stagger: 0.12 }, 0.5)
    .from(".fcard", { scale: 0.85, opacity: 0, duration: 1, stagger: 0.2 }, 0.9);

  ScrollTrigger.batch("[data-reveal]", {
    start: "top 88%", once: true,
    onEnter: (els) => gsap.to(els, { opacity: 1, y: 0, duration: 0.9, stagger: 0.12, ease: "power3.out" })
  });
  $$("[data-count]").forEach((el) => ScrollTrigger.create({
    trigger: el, start: "top 92%", once: true,
    onEnter: () => {
      const end = parseFloat(el.dataset.count), o = { v: 0 }, suf = el.dataset.suffix || "";
      const dec = suf.startsWith(".") ? 0 : 0;
      gsap.to(o, { v: end, duration: 2, ease: "power2.out", onUpdate: () => { el.textContent = Math.round(o.v) + suf; }, onComplete: () => { el.textContent = end + suf; } });
    }
  }));
}

/* bars in the bento card */
const bars = $(".bars");
if (bars) for (let i = 0; i < 28; i++) {
  const b = document.createElement("span");
  b.style.animationDelay = (i * 0.07).toFixed(2) + "s";
  b.style.animationDuration = (1 + (i % 5) * 0.25) + "s";
  bars.appendChild(b);
}

/* tilt + spotlight on cards */
if (fine) $$(".tilt").forEach((c) => {
  c.addEventListener("mousemove", (e) => {
    const r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    c.style.setProperty("--mx", x * 100 + "%"); c.style.setProperty("--my", y * 100 + "%");
    if (!reduce) c.style.transform = "perspective(900px) rotateX(" + ((0.5 - y) * 8) + "deg) rotateY(" + ((x - 0.5) * 10) + "deg)";
  });
  c.addEventListener("mouseleave", () => { c.style.transform = ""; });
});

/* magnetic buttons */
if (fine && !reduce) $$(".magnetic").forEach((b) => {
  b.addEventListener("mousemove", (e) => {
    const r = b.getBoundingClientRect();
    b.style.transform = "translate(" + ((e.clientX - r.left - r.width / 2) * 0.22) + "px," + ((e.clientY - r.top - r.height / 2) * 0.28) + "px)";
  });
  b.addEventListener("mouseleave", () => { b.style.transform = ""; });
});

/* custom cursor */
if (fine) {
  const dot = $(".cur-dot"), ring = $(".cur-ring");
  let x = innerWidth / 2, y = innerHeight / 2, rx = x, ry = y;
  addEventListener("mousemove", (e) => { x = e.clientX; y = e.clientY; dot.style.transform = "translate(" + x + "px," + y + "px)"; });
  (function loop() { rx += (x - rx) * 0.18; ry += (y - ry) * 0.18; ring.style.transform = "translate(" + rx + "px," + ry + "px)"; requestAnimationFrame(loop); })();
  document.addEventListener("mouseover", (e) => ring.classList.toggle("big", !!e.target.closest("a,button,summary,.tilt")));
  document.body.classList.add("has-cursor");
}

/* scripted demo conversation */
const demo = $("#demoWin");
if (demo && "IntersectionObserver" in window) {
  const io = new IntersectionObserver((en) => {
    if (!en[0].isIntersecting) return;
    io.disconnect();
    $$(".dm", demo).forEach((m, i) => setTimeout(() => m.classList.add("in"), 500 + i * 1300));
  }, { threshold: 0.4 });
  io.observe(demo);
} else $$(".dm").forEach((m) => m.classList.add("in"));

/* ---------- chatbot ---------- */
const chat = $("#chat"), msgs = $("#msgs"), form = $("#chatForm"), input = $("#chatInput"), sendBtn = $("#sendBtn"), launcher = $("#launcher"), chips = $("#chips");
const history = [];
let busy = false, greeted = false;

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const md = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`(.+?)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
const toBottom = () => { msgs.scrollTop = msgs.scrollHeight; };

function bubble(role, html) {
  const row = document.createElement("div");
  row.className = "msg " + role;
  row.innerHTML = (role === "bot" ? '<span class="dot"></span>' : "") + '<div class="bub">' + html + "</div>";
  msgs.appendChild(row); toBottom();
  return row;
}
function reveal(el, text) {
  return new Promise((done) => {
    const parts = text.split(/(\s+)/); let i = 0, acc = "";
    const step = () => {
      acc += parts[i++] || ""; el.innerHTML = md(acc); toBottom();
      if (i < parts.length) setTimeout(step, reduce ? 0 : 20 + Math.random() * 30); else done();
    };
    step();
  });
}
function openChat() {
  chat.classList.add("open"); chat.setAttribute("aria-hidden", "false"); launcher.setAttribute("aria-expanded", "true");
  if (!greeted) { greeted = true; bubble("bot", "Hi, I'm <strong>Lumen</strong>. Ask me anything, or tap a suggestion below."); }
  setTimeout(() => input.focus(), 300);
}
function closeChat() {
  chat.classList.remove("open"); chat.setAttribute("aria-hidden", "true"); launcher.setAttribute("aria-expanded", "false"); launcher.focus();
}
$$("[data-open-chat]").forEach((b) => b.addEventListener("click", openChat));
launcher.addEventListener("click", () => (chat.classList.contains("open") ? closeChat() : openChat()));
$("#closeChat").addEventListener("click", closeChat);
addEventListener("keydown", (e) => { if (e.key === "Escape" && chat.classList.contains("open")) closeChat(); });
input.addEventListener("input", () => window.orbPulse());

async function send(text) {
  if (busy || !text.trim()) return;
  busy = true; sendBtn.disabled = true; chips.style.display = "none";
  bubble("user", md(text)); history.push({ role: "user", content: text });
  input.value = "";
  const typing = bubble("bot", '<span class="typing"><i></i><i></i><i></i></span>');
  orbSet("thinking");
  let reply = "Sorry, something went wrong. Please try again.";
  try {
    const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ messages: history.slice(-12) }) });
    const data = await res.json();
    if (data.reply) reply = data.reply;
    if (data.mode === "demo") $("#mode").textContent = "Demo mode \u00b7 connect an API key for live AI";
  } catch (err) { console.warn(err); }
  const bub = $(".bub", typing);
  orbSet("speaking");
  await reveal(bub, reply);
  history.push({ role: "assistant", content: reply });
  orbSet("idle");
  busy = false; sendBtn.disabled = false; input.focus();
}
form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
$$(".chip").forEach((c) => c.addEventListener("click", () => send(c.textContent)));
})();
</script>
</body>
</html>
'''


if __name__ == "__main__":
    app.run(debug=True)
