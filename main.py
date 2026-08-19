import os
import uuid
import shutil
from pathlib import Path

from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Video Downloader</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>

:root{
    --green:#10b981;
    --green2:#059669;
    --dark:#07090e;
    --card:#111827;
    --card2:#0b1220;
    --border:#263247;
    --white:#f8fafc;
    --muted:#94a3b8;
}

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:"Outfit",sans-serif;
}

body{
    min-height:100vh;
    background:
        radial-gradient(circle at top,#12251f 0%,#07090e 45%);
    color:var(--white);
}

header{
    height:70px;
    display:flex;
    align-items:center;
    padding:0 25px;
    border-bottom:1px solid var(--border);
    background:rgba(17,24,39,.85);
    backdrop-filter:blur(15px);
}

.logo{
    color:white;
    text-decoration:none;
    font-size:23px;
    font-weight:800;
}

.logo span{
    color:var(--green);
}

main{
    width:100%;
    max-width:900px;
    margin:auto;
    padding:55px 16px;
}

.hero{
    text-align:center;
}

.hero h1{
    font-size:48px;
    font-weight:800;
    line-height:1.1;
    background:linear-gradient(
        135deg,
        #fff,
        #a7f3d0,
        #10b981
    );
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.hero p{
    margin-top:15px;
    color:var(--muted);
    font-size:16px;
}

.platforms{
    display:flex;
    justify-content:center;
    flex-wrap:wrap;
    gap:10px;
    margin:28px 0;
}

.platform{
    background:var(--card);
    border:1px solid var(--border);
    padding:8px 15px;
    border-radius:30px;
    color:#dbeafe;
    font-size:14px;
}

.search-box{
    background:rgba(17,24,39,.9);
    border:1px solid var(--border);
    border-radius:18px;
    padding:18px;
    box-shadow:0 20px 50px rgba(0,0,0,.35);
}

.input-row{
    display:flex;
    gap:10px;
}

#videoUrl{
    flex:1;
    min-width:0;
    background:#080d17;
    border:1px solid var(--border);
    color:white;
    border-radius:11px;
    padding:16px;
    outline:none;
    font-size:15px;
}

#videoUrl:focus{
    border-color:var(--green);
    box-shadow:0 0 18px rgba(16,185,129,.2);
}

.fetch{
    border:none;
    border-radius:11px;
    padding:0 23px;
    background:linear-gradient(
        135deg,
        var(--green),
        var(--green2)
    );
    color:white;
    font-weight:700;
    cursor:pointer;
    font-size:15px;
}

.fetch:hover{
    transform:translateY(-1px);
}

.status{
    display:none;
    margin-top:13px;
    padding:11px;
    text-align:center;
    border-radius:9px;
    background:#101b2c;
    color:#a7f3d0;
    font-size:14px;
}

.status.error{
    color:#fecaca;
}

.result{
    display:none;
    margin-top:25px;
    background:rgba(17,24,39,.95);
    border:1px solid var(--border);
    border-radius:18px;
    padding:20px;
}

.preview{
    display:grid;
    grid-template-columns:300px 1fr;
    gap:20px;
    padding-bottom:20px;
    border-bottom:1px solid var(--border);
}

.thumbnail{
    width:100%;
    aspect-ratio:16/9;
    object-fit:cover;
    background:#000;
    border-radius:12px;
}

.video-title{
    font-size:20px;
    font-weight:700;
    line-height:1.35;
    margin-bottom:12px;
}

.info{
    color:var(--muted);
    line-height:1.9;
    font-size:14px;
}

.tabs{
    display:flex;
    gap:10px;
    margin:20px 0 15px;
}

.tab{
    border:1px solid var(--border);
    background:#080d17;
    color:var(--muted);
    padding:9px 18px;
    border-radius:8px;
    cursor:pointer;
    font-weight:600;
}

.tab.active{
    background:var(--green);
    color:#00150e;
    border-color:var(--green);
}

.format-list{
    display:flex;
    flex-direction:column;
    gap:10px;
}

.format{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:15px;
    background:#090f1b;
    border:1px solid var(--border);
    border-radius:11px;
    padding:13px 15px;
}

.format-left{
    display:flex;
    align-items:center;
    gap:12px;
}

.badge{
    background:#334155;
    padding:5px 9px;
    border-radius:6px;
    font-size:12px;
    font-weight:800;
}

.badge.green{
    background:#059669;
    color:white;
}

.badge.blue{
    background:#0284c7;
    color:white;
}

.badge.purple{
    background:#7c3aed;
    color:white;
}

.download{
    text-decoration:none;
    white-space:nowrap;
    background:linear-gradient(
        135deg,
        var(--green),
        var(--green2)
    );
    color:white;
    padding:8px 15px;
    border-radius:8px;
    font-size:13px;
    font-weight:700;
}

.download:hover{
    filter:brightness(1.1);
}

footer{
    border-top:1px solid var(--border);
    text-align:center;
    color:var(--muted);
    padding:25px 15px;
    font-size:14px;
}

footer strong{
    color:#d1fae5;
}

@media(max-width:700px){

    main{
        padding-top:35px;
    }

    .hero h1{
        font-size:36px;
    }

    .input-row{
        flex-direction:column;
    }

    .fetch{
        padding:15px;
    }

    .preview{
        grid-template-columns:1fr;
    }

    .thumbnail{
        max-height:230px;
    }

    .format{
        padding:12px;
    }

    .format-left{
        gap:8px;
    }

    .download{
        padding:8px 10px;
    }
}

</style>
</head>

<body>

<header>

<a href="/" class="logo">
    Video<span>Downloader</span>
</a>

</header>


<main>

<section class="hero">

<h1>Video Downloader</h1>

<p>
Download videos from supported public video platforms
</p>

<div class="platforms">

<div class="platform">▶ YouTube</div>
<div class="platform">🎬 Shorts</div>
<div class="platform">📱 Instagram</div>
<div class="platform">📘 Facebook</div>

</div>

</section>


<section class="search-box">

<div class="input-row">

<input
    id="videoUrl"
    type="url"
    placeholder="Paste video link here..."
>

<button
    class="fetch"
    onclick="getVideoInfo()"
>
    Get Download
</button>

</div>

<div id="status" class="status"></div>

</section>


<section id="result" class="result">

<div class="preview">

<img
    id="thumbnail"
    class="thumbnail"
    src=""
    alt="Video thumbnail"
>

<div>

<div id="title" class="video-title">
    Video
</div>

<div id="info" class="info"></div>

</div>

</div>


<div class="tabs">

<button
    class="tab active"
    onclick="changeTab('video',this)"
>
Video
</button>

<button
    class="tab"
    onclick="changeTab('audio',this)"
>
Audio MP3
</button>

</div>


<div id="videoFormats" class="format-list"></div>

<div
    id="audioFormats"
    class="format-list"
    style="display:none"
></div>

</section>

</main>


<footer>

© 2026 Video Downloader
•
Developed by <strong>Arun Rohilla</strong>

</footer>


<script>

let currentUrl = "";


function status(message,error=false){

    const box=document.getElementById("status");

    box.style.display="block";
    box.innerText=message;

    if(error){
        box.classList.add("error");
    }else{
        box.classList.remove("error");
    }

}


async function getVideoInfo(){

    const url=document
        .getElementById("videoUrl")
        .value
        .trim();

    if(!url){

        status(
            "Please video link paste karein.",
            true
        );

        return;
    }

    currentUrl=url;

    document.getElementById("result")
        .style.display="none";

    status(
        "Video information fetch ho rahi hai..."
    );

    try{

        const response=await fetch(
            "/api/info",
            {
                method:"POST",

                headers:{
                    "Content-Type":
                        "application/json"
                },

                body:JSON.stringify({
                    url:url
                })
            }
        );

        const data=await response.json();

        if(!response.ok || !data.success){

            throw new Error(
                data.error ||
                "Video information nahi mili."
            );

        }


        document.getElementById("title")
            .innerText=data.title || "Video";


        const thumbnail=
            document.getElementById("thumbnail");

        thumbnail.src=
            data.thumbnail || "";


        document.getElementById("info")
            .innerHTML=
            "Platform: <b>"+
            safe(data.platform)+
            "</b><br>"+
            "Duration: <b>"+
            safe(data.duration)+
            "</b>";


        createVideoFormats(data.formats);

        createAudioFormats();


        document.getElementById("result")
            .style.display="block";


        status(
            "Download options ready hain."
        );

    }catch(error){

        status(
            error.message,
            true
        );

    }

}


function createVideoFormats(formats){

    const box=
        document.getElementById("videoFormats");

    box.innerHTML="";


    if(!formats || formats.length===0){

        box.innerHTML=
            "<div class='format'>"+
            "Compatible video format nahi mila."+
            "</div>";

        return;
    }


    formats.forEach(format=>{

        let badgeClass="";

        if(format.height>=1440){
            badgeClass="purple";
        }
        else if(format.height>=1080){
            badgeClass="blue";
        }
        else if(format.height>=720){
            badgeClass="green";
        }


        const row=
            document.createElement("div");

        row.className="format";


        row.innerHTML=`

            <div class="format-left">

                <span class="badge ${badgeClass}">
                    ${format.height}p
                </span>

                <div>
                    <b>${format.height}p MP4</b>
                    <br>
                    <small style="color:#94a3b8">
                        Video Quality
                    </small>
                </div>

            </div>

            <a
                class="download"
                href="/download?url=${encodeURIComponent(currentUrl)}&height=${format.height}"
            >
                Download
            </a>

        `;


        box.appendChild(row);

    });

}


function createAudioFormats(){

    const box=
        document.getElementById("audioFormats");

    box.innerHTML="";


    ["320","192","128"].forEach(rate=>{

        const row=
            document.createElement("div");

        row.className="format";


        row.innerHTML=`

            <div class="format-left">

                <span class="badge purple">
                    ${rate}K
                </span>

                <div>
                    <b>MP3 Audio</b>
                    <br>
                    <small style="color:#94a3b8">
                        ${rate} kbps
                    </small>
                </div>

            </div>

            <a
                class="download"
                href="/download?url=${encodeURIComponent(currentUrl)}&audio=1&bitrate=${rate}"
            >
                Download MP3
            </a>

        `;


        box.appendChild(row);

    });

}


function changeTab(type,button){

    document
        .querySelectorAll(".tab")
        .forEach(btn=>{
            btn.classList.remove("active");
        });


    button.classList.add("active");


    const video=
        document.getElementById("videoFormats");

    const audio=
        document.getElementById("audioFormats");


    if(type==="video"){

        video.style.display="flex";
        audio.style.display="none";

    }else{

        video.style.display="none";
        audio.style.display="flex";

    }

}


function safe(value){

    return String(value || "")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");

}

</script>

</body>
</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template_string(HTML)


# ============================================================
# VIDEO INFORMATION
# ============================================================

@app.route("/api/info", methods=["POST"])
def api_info():

    data=request.get_json(silent=True) or {}

    url=(data.get("url") or "").strip()

    if not url:

        return jsonify({
            "success":False,
            "error":"URL required hai."
        }),400


    try:

        options={
            "quiet":True,
            "no_warnings":True,
            "skip_download":True,
            "noplaylist":True,
        }


        with yt_dlp.YoutubeDL(options) as ydl:

            info=ydl.extract_info(
                url,
                download=False
            )


        formats=[]

        wanted=[
            144,
            240,
            360,
            480,
            720,
            1080,
            1440
        ]


        for fmt in info.get(
            "formats",
            []
        ):

            height=fmt.get("height")

            if not height:
                continue

            if height not in wanted:
                continue

            if fmt.get("vcodec") in [
                None,
                "none"
            ]:
                continue

            formats.append({
                "height":height,
                "ext":fmt.get(
                    "ext",
                    "mp4"
                )
            })


        unique={}

        for item in formats:

            unique[item["height"]]=item


        formats=list(unique.values())

        formats.sort(
            key=lambda x:x["height"],
            reverse=True
        )


        duration=info.get("duration")

        if duration:

            mins=int(duration//60)
            secs=int(duration%60)

            duration_text=\
                f"{mins}:{secs:02d}"

        else:

            duration_text="Unknown"


        return jsonify({

            "success":True,

            "title":
                info.get(
                    "title",
                    "Video"
                ),

            "thumbnail":
                info.get(
                    "thumbnail",
                    ""
                ),

            "duration":
                duration_text,

            "platform":
                info.get(
                    "extractor_key",
                    "Video"
                ),

            "formats":
                formats

        })


    except Exception as e:

        return jsonify({

            "success":False,

            "error":
                "Video fetch failed: "
                + str(e)

        }),500


# ============================================================
# DOWNLOAD
# ============================================================

@app.route("/download")
def download():

    url=request.args.get(
        "url",
        ""
    ).strip()

    height=request.args.get(
        "height",
        "720"
    )

    audio=request.args.get(
        "audio"
    )

    bitrate=request.args.get(
        "bitrate",
        "192"
    )


    if not url:

        return "URL missing",400


    job=uuid.uuid4().hex

    output=str(
        DOWNLOAD_DIR /
        f"{job}.%(ext)s"
    )


    try:

        if audio=="1":

            options={

                "format":
                    "bestaudio/best",

                "outtmpl":
                    output,

                "noplaylist":
                    True,

                "quiet":
                    True,

                "postprocessors":[

                    {
                        "key":
                            "FFmpegExtractAudio",

                        "preferredcodec":
                            "mp3",

                        "preferredquality":
                            bitrate
                    }

                ]

            }

        else:

            max_height=int(height)

            options={

                "format":
                    f"bestvideo[height<={max_height}]"
                    f"+bestaudio/"
                    f"best[height<={max_height}]",

                "outtmpl":
                    output,

                "merge_output_format":
                    "mp4",

                "noplaylist":
                    True,

                "quiet":
                    True

            }


        with yt_dlp.YoutubeDL(options) as ydl:

            info=ydl.extract_info(
                url,
                download=True
            )


        # Find generated file
        files=list(
            DOWNLOAD_DIR.glob(
                f"{job}.*"
            )
        )


        if not files:

            return (
                "Downloaded file nahi mili.",
                500
            )


        file_path=files[0]


        if audio=="1":

            download_name="audio.mp3"

        else:

            download_name="video.mp4"


        response=send_file(

            file_path,

            as_attachment=True,

            download_name=download_name

        )


        # Delete after response
        @response.call_on_close
        def cleanup():

            try:

                if file_path.exists():
                    file_path.unlink()

            except Exception:
                pass


        return response


    except Exception as e:

        # Cleanup failed job files
        for file in DOWNLOAD_DIR.glob(
            f"{job}.*"
        ):

            try:
                file.unlink()
            except Exception:
                pass


        return (
            "Download failed: "
            + str(e),
            500
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status":"ok",
        "site":"Video Downloader",
        "developer":"Arun Rohilla"
    })


# ============================================================
# START
# ============================================================

if __name__=="__main__":

    port=int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
        )
