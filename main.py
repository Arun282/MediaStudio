import os
import uuid
import time
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

COOKIE_FILE = Path("cookies.txt")
PROXY_URL = os.getenv("PROXY_URL", "").strip()
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2"))
_last_request = 0.0


def platform_of(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "youtu.be" in host or "youtube.com" in host:
        return "YouTube"
    if "instagram.com" in host:
        return "Instagram"
    if "facebook.com" in host or "fb.watch" in host:
        return "Facebook"
    return "Other"


def throttle():
    global _last_request
    now = time.time()
    wait = REQUEST_DELAY - (now - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.time()


def ydl_opts(url, download=False):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": not download,
        "retries": 1,
        "fragment_retries": 1,
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # Current yt-dlp needs a supported JS runtime for full YouTube support.
    # Deno is installed by the Dockerfile and enabled here.
    opts["js_runtimes"] = {"deno": None}

    if COOKIE_FILE.exists():
        opts["cookiefile"] = str(COOKIE_FILE)

    if PROXY_URL:
        opts["proxy"] = PROXY_URL

    return opts


def friendly_error(exc, platform):
    text = str(exc)
    low = text.lower()

    if "429" in text or "too many requests" in low:
        return (
            f"{platform} ne server IP ko rate-limit kiya hai (HTTP 429). "
            "Code request ko repeatedly retry nahi karega. "
            "Agar ye Render par hota rahe, same platform ke authorized "
            "cookies/whitelisted proxy ki zarurat ho sakti hai."
        )

    if "login required" in low or "authentication" in low:
        return f"{platform} login/authentication required hai."

    if "private" in low:
        return "Ye video private hai ya public access available nahi hai."

    if "ffmpeg" in low:
        return "FFmpeg server par available nahi hai."

    if "javascript runtime" in low or "no supported javascript" in low:
        return (
            "YouTube ke liye JavaScript runtime unavailable hai. "
            "Docker deployment use karein; is project me Deno included hai."
        )

    if "unsupported url" in low:
        return "Ye URL supported nahi hai."

    return f"{platform} request failed: {text[:450]}"


def extract(url, download=False, extra=None):
    options = ydl_opts(url, download)
    if extra:
        options.update(extra)
    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=download)


HTML = r"""
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Video Downloader</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--p:#10b981;--p2:#059669;--bg:#07090e;--card:#111827;--border:#263247;--muted:#94a3b8}
*{box-sizing:border-box;margin:0;padding:0;font-family:Outfit,sans-serif}
body{min-height:100vh;color:#f8fafc;background:radial-gradient(circle at top,#12352b,#07090e 48%)}
header{height:72px;padding:0 22px;display:flex;align-items:center;background:#111827ee;border-bottom:1px solid var(--border)}
.logo{font-size:24px;font-weight:800;color:white}.logo span{color:var(--p)}
main{max-width:900px;margin:auto;padding:48px 15px}
.hero{text-align:center}.hero h1{font-size:48px;line-height:1.1;background:linear-gradient(135deg,#fff,#a7f3d0,#10b981);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.hero p{margin:14px auto 0;color:var(--muted);max-width:620px;font-size:17px}
.platforms{display:flex;justify-content:center;flex-wrap:wrap;gap:10px;margin:28px 0}
.platform{background:#111827;border:1px solid var(--border);padding:10px 18px;border-radius:40px}
.card{background:#111827f2;border:1px solid var(--border);border-radius:18px;padding:18px}
.input-row{display:flex;gap:10px}input{flex:1;background:#080d17;color:white;border:1px solid var(--border);border-radius:12px;padding:16px;font-size:15px;outline:none}input:focus{border-color:var(--p)}
button{cursor:pointer}.fetch{border:0;border-radius:12px;padding:0 25px;color:#fff;font-size:15px;font-weight:700;background:linear-gradient(135deg,var(--p),var(--p2))}
.fetch:disabled{opacity:.6}
.status{display:none;margin-top:14px;background:#0d1929;border-radius:12px;padding:14px;text-align:center;color:#a7f3d0;line-height:1.5}.status.error{color:#fca5a5}
.result{display:none;margin-top:24px}.preview{display:grid;grid-template-columns:300px 1fr;gap:20px;padding-bottom:20px;border-bottom:1px solid var(--border)}
.thumb{width:100%;aspect-ratio:16/9;object-fit:cover;background:#000;border-radius:12px}.title{font-size:21px;font-weight:700;line-height:1.35;margin-bottom:10px}.info{color:var(--muted);line-height:1.8}
.tabs{display:flex;gap:10px;margin:20px 0 14px}.tab{background:#080d17;color:var(--muted);border:1px solid var(--border);padding:9px 18px;border-radius:9px;font-weight:700}.tab.active{background:var(--p);color:#00150e;border-color:var(--p)}
.list{display:flex;flex-direction:column;gap:10px}.row{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#090f1b;border:1px solid var(--border);padding:13px 15px;border-radius:11px}.left{display:flex;align-items:center;gap:12px}.badge{background:#334155;border-radius:6px;padding:5px 9px;font-size:12px;font-weight:800}.green{background:#059669}.blue{background:#0284c7}.purple{background:#7c3aed}.dl{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;text-decoration:none;padding:8px 14px;border-radius:8px;font-size:13px;font-weight:700;white-space:nowrap}
footer{border-top:1px solid var(--border);text-align:center;color:var(--muted);padding:25px;margin-top:25px}footer b{color:#d1fae5}
@media(max-width:700px){main{padding-top:35px}.hero h1{font-size:37px}.input-row{flex-direction:column}.fetch{padding:15px}.preview{grid-template-columns:1fr}.thumb{max-height:240px}.row{padding:12px}.dl{padding:8px 10px}}
</style>
</head>
<body>
<header><div class="logo">Video<span>Downloader</span></div></header>
<main>
<section class="hero">
<h1>Video Downloader</h1>
<p>Download supported public videos in different qualities</p>
<div class="platforms"><div class="platform">▶ YouTube</div><div class="platform">🎬 Shorts</div><div class="platform">📱 Instagram</div><div class="platform">📘 Facebook</div></div>
</section>
<section class="card">
<div class="input-row">
<input id="url" type="url" placeholder="Video link yahan paste karein...">
<button id="fetch" class="fetch" onclick="loadInfo()">Get Download</button>
</div>
<div id="status" class="status"></div>
</section>
<section id="result" class="card result">
<div class="preview">
<img id="thumb" class="thumb" alt="thumbnail">
<div><div id="title" class="title"></div><div id="info" class="info"></div></div>
</div>
<div class="tabs"><button class="tab active" onclick="tab('video',this)">Video</button><button class="tab" onclick="tab('audio',this)">Audio MP3</button></div>
<div id="videos" class="list"></div><div id="audios" class="list" style="display:none"></div>
</section>
</main>
<footer>© 2026 Video Downloader • Developed by <b>Arun Rohilla</b></footer>
<script>
let current="";
function status(msg,error=false){let e=document.getElementById("status");e.style.display="block";e.className="status"+(error?" error":"");e.textContent=msg}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
async function loadInfo(){
 current=document.getElementById("url").value.trim();let b=document.getElementById("fetch");
 if(!current){status("Video link paste karein.",true);return}
 b.disabled=true;b.textContent="Fetching...";document.getElementById("result").style.display="none";status("Video information fetch ho rahi hai...");
 try{
  let r=await fetch("/api/info",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:current})});
  let d=await r.json();if(!r.ok||!d.success)throw Error(d.error||"Video information nahi mili.");
  document.getElementById("title").textContent=d.title||"Video";
  document.getElementById("thumb").src=d.thumbnail||"";
  document.getElementById("info").innerHTML="Platform: <b>"+esc(d.platform)+"</b><br>Duration: <b>"+esc(d.duration)+"</b>";
  renderVideos(d.formats);renderAudios();document.getElementById("result").style.display="block";status("Download options ready hain.");
 }catch(e){status(e.message,true)}finally{b.disabled=false;b.textContent="Get Download"}
}
function renderVideos(fs){
 let box=document.getElementById("videos");box.innerHTML="";
 if(!fs.length){box.innerHTML="<div class='row'>Compatible video format nahi mila.</div>";return}
 fs.forEach(f=>{let c=f.height>=1440?"purple":f.height>=1080?"blue":f.height>=720?"green":"";
 box.insertAdjacentHTML("beforeend",`<div class="row"><div class="left"><span class="badge ${c}">${f.height}p</span><div><b>${f.height}p MP4</b><br><small style="color:#94a3b8">${esc(f.note||"Video quality")}</small></div></div><a class="dl" href="/download?url=${encodeURIComponent(current)}&height=${f.height}">Download</a></div>`)})
}
function renderAudios(){
 let b=document.getElementById("audios");b.innerHTML="";
 ["320","192","128"].forEach(q=>b.insertAdjacentHTML("beforeend",`<div class="row"><div class="left"><span class="badge purple">${q}K</span><b>MP3 Audio</b></div><a class="dl" href="/download?url=${encodeURIComponent(current)}&audio=1&bitrate=${q}">Download MP3</a></div>`))
}
function tab(t,el){document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));el.classList.add("active");document.getElementById("videos").style.display=t==="video"?"flex":"none";document.getElementById("audios").style.display=t==="audio"?"flex":"none"}
</script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(HTML)


@app.post("/api/info")
def api_info():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url") or "").strip()

    if not url:
        return jsonify(success=False, error="URL required hai."), 400

    platform = platform_of(url)
    if platform == "Other":
        return jsonify(success=False, error="YouTube, Instagram ya Facebook URL dein."), 400

    try:
        throttle()
        info = extract(url, download=False)

        # Some extractors return an entries wrapper.
        if not info.get("formats") and info.get("entries"):
            entries = [e for e in info["entries"] if e]
            if entries:
                info = entries[0]

        wanted = [144, 240, 360, 480, 720, 1080, 1440]
        formats = {}

        for f in info.get("formats") or []:
            h = f.get("height")
            if h not in wanted or f.get("vcodec") in (None, "none"):
                continue
            formats[h] = {
                "height": int(h),
                "note": "MP4 / Video"
            }

        # If the extractor only exposes a pre-merged format, expose it as Best.
        if not formats:
            has_video = any(
                f.get("vcodec") not in (None, "none")
                for f in (info.get("formats") or [])
            )
            if has_video:
                formats[0] = {"height": 0, "note": "Best available"}

        out = sorted(formats.values(), key=lambda x: x["height"], reverse=True)

        duration = info.get("duration")
        duration_text = "Unknown"
        if duration:
            duration_text = f"{int(duration)//60}:{int(duration)%60:02d}"

        return jsonify(
            success=True,
            title=info.get("title") or "Video",
            thumbnail=info.get("thumbnail") or "",
            duration=duration_text,
            platform=platform,
            formats=out,
        )

    except Exception as exc:
        return jsonify(success=False, error=friendly_error(exc, platform)), 502


@app.get("/download")
def download():
    url = str(request.args.get("url") or "").strip()
    if not url:
        return "URL missing", 400

    platform = platform_of(url)
    audio = request.args.get("audio") == "1"
    requested_height = int(request.args.get("height") or 720)
    bitrate = request.args.get("bitrate", "192")

    job = uuid.uuid4().hex
    output = str(DOWNLOAD_DIR / f"{job}.%(ext)s")

    try:
        throttle()
        extra = {"outtmpl": output}

        if audio:
            extra.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(bitrate),
                }],
            })
            filename = "audio.mp3"
        else:
            if requested_height <= 0:
                fmt = "bestvideo*+bestaudio/best"
            else:
                fmt = (
                    f"bestvideo[height<={requested_height}]+bestaudio/"
                    f"best[height<={requested_height}]/best"
                )
            extra.update({
                "format": fmt,
                "merge_output_format": "mp4",
            })
            filename = "video.mp4"

        extract(url, download=True, extra=extra)

        files = list(DOWNLOAD_DIR.glob(f"{job}.*"))
        if not files:
            return "Downloaded file nahi mili.", 500

        wanted = DOWNLOAD_DIR / (f"{job}.mp3" if audio else f"{job}.mp4")
        path = wanted if wanted.exists() else files[0]

        response = send_file(path, as_attachment=True, download_name=filename)

        @response.call_on_close
        def cleanup():
            for p in DOWNLOAD_DIR.glob(f"{job}.*"):
                try:
                    p.unlink()
                except OSError:
                    pass

        return response

    except Exception as exc:
        for p in DOWNLOAD_DIR.glob(f"{job}.*"):
            try:
                p.unlink()
            except OSError:
                pass
        return friendly_error(exc, platform), 502


@app.get("/health")
def health():
    try:
        import shutil
        deno = shutil.which("deno")
        ffmpeg = shutil.which("ffmpeg")
    except Exception:
        deno = ffmpeg = None

    return jsonify(
        status="ok",
        site="Video Downloader",
        developer="Arun Rohilla",
        yt_dlp=yt_dlp.version.__version__,
        deno=deno or "not found",
        ffmpeg=ffmpeg or "not found",
        proxy_configured=bool(PROXY_URL),
        cookies_configured=COOKIE_FILE.exists(),
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
