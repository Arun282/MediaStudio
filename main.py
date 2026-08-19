import os
import uuid
import tempfile
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
PROXY_URL = os.environ.get("PROXY_URL", "").strip()
INSTAGRAM_COOKIES = os.environ.get("INSTAGRAM_COOKIES", "").strip()


def get_platform(url):
    host = urlparse(url).netloc.lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "YouTube"
    if "instagram.com" in host:
        return "Instagram"
    if "facebook.com" in host or "fb.watch" in host:
        return "Facebook"
    return "Other"


def get_cookie_file():
    if COOKIE_FILE.exists():
        return str(COOKIE_FILE)

    if INSTAGRAM_COOKIES:
        cookie_path = Path(tempfile.gettempdir()) / "instagram_cookies.txt"
        try:
            cookie_path.write_text(INSTAGRAM_COOKIES, encoding="utf-8")
            return str(cookie_path)
        except Exception:
            return None

    return None


def ydl_options(url, skip_download=False):
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 2,
        "fragment_retries": 2,
        "skip_download": skip_download,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    platform = get_platform(url)

    if platform == "Instagram":
        cookie_file = get_cookie_file()
        if cookie_file:
            options["cookiefile"] = cookie_file

    if PROXY_URL:
        options["proxy"] = PROXY_URL

    return options


def clean_error(error):
    text = str(error)

    if "429" in text or "Too Many Requests" in text:
        return (
            "Instagram ne request limit kar di hai (HTTP 429). "
            "Public access/login/rate-limit ki wajah se request reject hui."
        )

    if "login required" in text.lower():
        return "Instagram login required hai."

    if "private" in text.lower():
        return "Ye content private hai ya public access available nahi hai."

    if "Unsupported URL" in text:
        return "Ye URL supported nahi hai."

    return "Request failed: " + text[:500]


HTML = r"""
<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Video Downloader</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--p:#10b981;--p2:#059669;--bg:#07090e;--card:#111827;--b:#263247;--m:#94a3b8}
*{box-sizing:border-box;margin:0;padding:0;font-family:Outfit,sans-serif}
body{min-height:100vh;background:radial-gradient(circle at top,#12352b,#07090e 45%);color:#f8fafc}
header{height:70px;padding:0 22px;display:flex;align-items:center;background:#111827dd;border-bottom:1px solid var(--b)}
.logo{font-size:23px;font-weight:800;color:#fff;text-decoration:none}.logo span{color:var(--p)}
main{max-width:900px;margin:auto;padding:50px 15px}.hero{text-align:center}
.hero h1{font-size:48px;line-height:1.1;background:linear-gradient(135deg,#fff,#a7f3d0,#10b981);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{margin-top:15px;color:var(--m)}
.platforms{display:flex;justify-content:center;flex-wrap:wrap;gap:10px;margin:28px 0}
.platform{background:var(--card);border:1px solid var(--b);border-radius:40px;padding:9px 16px}
.search-box,.result{background:#111827f2;border:1px solid var(--b);border-radius:18px;padding:18px}
.search-box{box-shadow:0 20px 55px #0006}.input-row{display:flex;gap:10px}
#videoUrl{flex:1;background:#080d17;border:1px solid var(--b);color:#fff;border-radius:11px;padding:16px;outline:none;font-size:15px}
#videoUrl:focus{border-color:var(--p)}
.fetch{border:0;border-radius:11px;padding:0 23px;color:#fff;font-size:15px;font-weight:700;cursor:pointer;background:linear-gradient(135deg,var(--p),var(--p2))}
.fetch:disabled{opacity:.6}
.status{display:none;margin-top:14px;padding:12px;border-radius:10px;text-align:center;background:#101b2c;color:#a7f3d0;font-size:14px;line-height:1.5}.status.error{color:#fca5a5}
.result{display:none;margin-top:25px}.preview{display:grid;grid-template-columns:300px 1fr;gap:20px;padding-bottom:20px;border-bottom:1px solid var(--b)}
.thumbnail{width:100%;aspect-ratio:16/9;object-fit:cover;background:#000;border-radius:12px}
.video-title{font-size:20px;font-weight:700;line-height:1.4;margin-bottom:12px}.info{color:var(--m);line-height:1.9;font-size:14px}
.tabs{display:flex;gap:10px;margin:20px 0 15px}.tab{background:#080d17;color:var(--m);border:1px solid var(--b);padding:9px 18px;border-radius:8px;cursor:pointer;font-weight:600}.tab.active{background:var(--p);border-color:var(--p);color:#00150e}
.format-list{display:flex;flex-direction:column;gap:10px}.format{display:flex;justify-content:space-between;align-items:center;gap:15px;background:#090f1b;border:1px solid var(--b);border-radius:11px;padding:13px 15px}
.format-left{display:flex;align-items:center;gap:12px}.badge{padding:5px 9px;border-radius:6px;font-size:12px;font-weight:800;background:#334155}.green{background:#059669}.blue{background:#0284c7}.purple{background:#7c3aed}
.download{text-decoration:none;white-space:nowrap;color:#fff;background:linear-gradient(135deg,var(--p),var(--p2));padding:8px 15px;border-radius:8px;font-size:13px;font-weight:700}
footer{margin-top:30px;border-top:1px solid var(--b);text-align:center;color:var(--m);padding:25px 15px;font-size:14px}footer strong{color:#d1fae5}
@media(max-width:700px){main{padding-top:35px}.hero h1{font-size:36px}.input-row{flex-direction:column}.fetch{padding:15px}.preview{grid-template-columns:1fr}.thumbnail{max-height:230px}.format{padding:12px}.download{padding:8px 10px}}
</style>
</head>
<body>
<header><a href="/" class="logo">Video<span>Downloader</span></a></header>
<main>
<section class="hero">
<h1>Video Downloader</h1>
<p>Download supported public videos in different qualities</p>
<div class="platforms">
<div class="platform">▶ YouTube</div><div class="platform">🎬 Shorts</div>
<div class="platform">📱 Instagram</div><div class="platform">📘 Facebook</div>
</div>
</section>
<section class="search-box">
<div class="input-row">
<input id="videoUrl" type="url" placeholder="Video link yahan paste karein...">
<button id="fetchBtn" class="fetch" onclick="getVideoInfo()">Get Download</button>
</div>
<div id="status" class="status"></div>
</section>
<section id="result" class="result">
<div class="preview">
<img id="thumbnail" class="thumbnail" src="" alt="Video thumbnail">
<div><div id="title" class="video-title">Video</div><div id="info" class="info"></div></div>
</div>
<div class="tabs">
<button class="tab active" onclick="changeTab('video',this)">Video</button>
<button class="tab" onclick="changeTab('audio',this)">Audio MP3</button>
</div>
<div id="videoFormats" class="format-list"></div>
<div id="audioFormats" class="format-list" style="display:none"></div>
</section>
</main>
<footer>© 2026 Video Downloader • Developed by <strong>Arun Rohilla</strong></footer>
<script>
let currentUrl="";
function showStatus(message,error=false){
 const box=document.getElementById("status");box.style.display="block";box.innerText=message;box.classList.toggle("error",error);
}
async function getVideoInfo(){
 const url=document.getElementById("videoUrl").value.trim();
 const button=document.getElementById("fetchBtn");
 if(!url){showStatus("Please video link paste karein.",true);return;}
 currentUrl=url;button.disabled=true;button.innerText="Fetching...";
 document.getElementById("result").style.display="none";
 showStatus("Video information fetch ho rahi hai...");
 try{
  const response=await fetch("/api/info",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});
  const data=await response.json();
  if(!response.ok||!data.success)throw new Error(data.error||"Video information nahi mili.");
  document.getElementById("title").innerText=data.title||"Video";
  if(data.thumbnail)document.getElementById("thumbnail").src=data.thumbnail;
  document.getElementById("info").innerHTML="Platform: <b>"+safe(data.platform)+"</b><br>Duration: <b>"+safe(data.duration)+"</b>";
  createVideoFormats(data.formats);createAudioFormats();
  document.getElementById("result").style.display="block";showStatus("Download options ready hain.");
 }catch(error){showStatus(error.message,true)}
 finally{button.disabled=false;button.innerText="Get Download";}
}
function createVideoFormats(formats){
 const box=document.getElementById("videoFormats");box.innerHTML="";
 if(!formats||!formats.length){box.innerHTML="<div class='format'>Compatible video format nahi mila.</div>";return;}
 formats.forEach(item=>{
  let badge=item.height>=1440?"purple":item.height>=1080?"blue":item.height>=720?"green":"";
  const row=document.createElement("div");row.className="format";
  row.innerHTML=`<div class="format-left"><span class="badge ${badge}">${item.height}p</span><div><b>${item.height}p MP4</b><br><small style="color:#94a3b8">Video Quality</small></div></div><a class="download" href="/download?url=${encodeURIComponent(currentUrl)}&height=${item.height}">Download</a>`;
  box.appendChild(row);
 });
}
function createAudioFormats(){
 const box=document.getElementById("audioFormats");box.innerHTML="";
 ["320","192","128"].forEach(rate=>{
  const row=document.createElement("div");row.className="format";
  row.innerHTML=`<div class="format-left"><span class="badge purple">${rate}K</span><div><b>MP3 Audio</b><br><small style="color:#94a3b8">${rate} kbps</small></div></div><a class="download" href="/download?url=${encodeURIComponent(currentUrl)}&audio=1&bitrate=${rate}">Download MP3</a>`;
  box.appendChild(row);
 });
}
function changeTab(type,button){
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));button.classList.add("active");
 document.getElementById("videoFormats").style.display=type==="video"?"flex":"none";
 document.getElementById("audioFormats").style.display=type==="audio"?"flex":"none";
}
function safe(value){return String(value||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");}
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/info", methods=["POST"])
def api_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"success": False, "error": "URL required hai."}), 400

    platform = get_platform(url)

    if platform == "Other":
        return jsonify({
            "success": False,
            "error": "Ye platform currently supported nahi hai."
        }), 400

    try:
        options = ydl_options(url, skip_download=True)

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        wanted = [144, 240, 360, 480, 720, 1080, 1440]
        unique = {}

        for fmt in info.get("formats", []):
            height = fmt.get("height")
            if not height or height not in wanted:
                continue
            if fmt.get("vcodec") in (None, "none"):
                continue
            unique[height] = {
                "height": height,
                "ext": fmt.get("ext", "mp4")
            }

        formats = sorted(unique.values(), key=lambda x: x["height"], reverse=True)

        duration = info.get("duration")
        if duration:
            mins = int(duration // 60)
            secs = int(duration % 60)
            duration_text = f"{mins}:{secs:02d}"
        else:
            duration_text = "Unknown"

        return jsonify({
            "success": True,
            "title": info.get("title", "Video"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": duration_text,
            "platform": platform,
            "formats": formats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": clean_error(e)
        }), 500


@app.route("/download")
def download():
    url = request.args.get("url", "").strip()
    height = request.args.get("height", "720")
    audio = request.args.get("audio")
    bitrate = request.args.get("bitrate", "192")

    if not url:
        return "URL missing", 400

    job = uuid.uuid4().hex
    output = str(DOWNLOAD_DIR / f"{job}.%(ext)s")

    try:
        options = ydl_options(url)
        options["outtmpl"] = output

        if audio == "1":
            options["format"] = "bestaudio/best"
            options["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(bitrate)
            }]
            download_name = "audio.mp3"
        else:
            max_height = int(height)
            options["format"] = (
                f"bestvideo[height<={max_height}]+bestaudio/"
                f"best[height<={max_height}]"
            )
            options["merge_output_format"] = "mp4"
            download_name = "video.mp4"

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(url, download=True)

        files = list(DOWNLOAD_DIR.glob(f"{job}.*"))
        if not files:
            return "Downloaded file nahi mili.", 500

        if audio == "1":
            preferred = DOWNLOAD_DIR / f"{job}.mp3"
        else:
            preferred = DOWNLOAD_DIR / f"{job}.mp4"

        file_path = preferred if preferred.exists() else files[0]

        response = send_file(
            file_path,
            as_attachment=True,
            download_name=download_name
        )

        @response.call_on_close
        def cleanup():
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass

        return response

    except Exception as e:
        for file in DOWNLOAD_DIR.glob(f"{job}.*"):
            try:
                file.unlink()
            except Exception:
                pass

        return clean_error(e), 500


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "site": "Video Downloader",
        "developer": "Arun Rohilla",
        "yt_dlp": yt_dlp.version.__version__
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
