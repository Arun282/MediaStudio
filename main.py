import os
import re
import urllib.parse
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==============================================================================
# FULL MODERN FRONTEND (HTML + CSS + JS)
# ==============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Media & Reels Downloader</title>
    <!-- Fonts & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg-dark: #090d16;
            --card-bg: #131b2e;
            --card-border: #23304a;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --yt-color: #ff0000;
            --ig-color: #e1306c;
            --fb-color: #1877f2;
            --success: #22c55e;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; }

        /* Navbar */
        header {
            background: rgba(19, 27, 46, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--card-border);
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 1.3rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-main);
            text-decoration: none;
        }
        .logo i { color: var(--primary); }

        main {
            flex: 1;
            max-width: 900px;
            width: 100%;
            margin: 1.5rem auto;
            padding: 0 1rem;
        }

        .hero { text-align: center; margin-bottom: 1.8rem; }
        .hero h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            background: linear-gradient(135deg, #c7d2fe, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero p { color: var(--text-muted); font-size: 0.9rem; }

        .platform-badges {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 1.2rem 0;
            flex-wrap: wrap;
        }

        .badge {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.82rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .badge.yt i { color: var(--yt-color); }
        .badge.ig i { color: var(--ig-color); }
        .badge.fb i { color: var(--fb-color); }

        .search-box {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 1.2rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }

        .input-wrapper { display: flex; gap: 10px; }
        .input-wrapper input {
            flex: 1;
            background: #080c14;
            border: 1px solid var(--card-border);
            padding: 0.9rem 1.1rem;
            border-radius: 10px;
            color: var(--text-main);
            font-size: 0.95rem;
            outline: none;
            transition: border 0.3s;
        }
        .input-wrapper input:focus { border-color: var(--primary); }

        .btn-fetch {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 0 1.5rem;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
            white-space: nowrap;
        }
        .btn-fetch:hover { background: var(--primary-hover); }

        .result-container {
            display: none;
            margin-top: 1.5rem;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            animation: fadeIn 0.35s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .preview-layout {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--card-border);
        }

        .video-player-box {
            position: relative;
            width: 100%;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--card-border);
            min-height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .video-player-box.reel-mode { min-height: 380px; max-width: 260px; margin: 0 auto; }
        .video-player-box iframe, .video-player-box video, .video-player-box img {
            width: 100%; height: 100%; min-height: 180px; border: none; border-radius: 12px; object-fit: cover;
        }
        .video-player-box.reel-mode iframe { min-height: 380px; }

        .media-meta h3 { font-size: 1.1rem; margin-bottom: 0.5rem; line-height: 1.4; word-break: break-word; }
        .meta-tags { display: flex; gap: 8px; margin-bottom: 0.8rem; flex-wrap: wrap; }
        .tag-pill {
            background: #1e293b; color: var(--text-muted); padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 6px;
        }

        .format-nav {
            display: flex; gap: 10px; margin-bottom: 1.2rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.8rem;
        }
        .f-btn {
            background: transparent; border: 1px solid var(--card-border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 500; display: flex; align-items: center; gap: 8px;
        }
        .f-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }

        .quality-grid { display: flex; flex-direction: column; gap: 10px; }
        .q-card {
            display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #090d16; border: 1px solid var(--card-border); border-radius: 10px;
        }
        .q-left { display: flex; align-items: center; gap: 12px; }

        .badge-res { padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; background: #334155; }
        .badge-res.uhd { background: #7c3aed; color: #fff; }
        .badge-res.fhd { background: #0284c7; color: #fff; }
        .badge-res.hd { background: #059669; color: #fff; }

        .btn-dl {
            background: var(--success); color: #fff; padding: 7px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; border: none; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: background 0.2s;
        }
        .btn-dl:hover { background: #16a34a; }

        .spinner { display: none; margin: 2rem auto; text-align: center; }
        .spinner i { font-size: 2rem; color: var(--primary); animation: spin 1s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        footer { text-align: center; padding: 1.2rem; color: var(--text-muted); font-size: 0.8rem; border-top: 1px solid var(--card-border); margin-top: auto; }
        @media (max-width: 700px) { .preview-layout { grid-template-columns: 1fr; } .input-wrapper { flex-direction: column; } }
    </style>
</head>
<body>

    <header>
        <a href="#" class="logo"><i class="fa-solid fa-play-circle"></i> MediaStudio</a>
    </header>

    <main>
        <section class="hero">
            <h1>Universal Video & Audio Downloader</h1>
            <p>Direct download in 144p to 2K (1440p) with live stream preview</p>
            <div class="platform-badges">
                <div class="badge yt"><i class="fa-brands fa-youtube"></i> YouTube & Shorts</div>
                <div class="badge ig"><i class="fa-brands fa-instagram"></i> Instagram Reels</div>
                <div class="badge fb"><i class="fa-brands fa-facebook"></i> Facebook Video</div>
            </div>
        </section>

        <section class="search-box">
            <div class="input-wrapper">
                <input type="text" id="videoUrl" placeholder="Paste link here (YouTube, Shorts, Reel, Facebook)...">
                <button class="btn-fetch" onclick="processDownloadRequest()">
                    <i class="fa-solid fa-bolt"></i> Get Media
                </button>
            </div>
        </section>

        <div class="spinner" id="loader">
            <i class="fa-solid fa-circle-notch"></i>
            <p style="margin-top: 8px; font-size: 0.9rem; color: var(--text-muted);">Fetching live streams & download links...</p>
        </div>

        <section class="result-container" id="resultContainer">
            <div class="preview-layout">
                <div class="video-player-box" id="playerWrapper"></div>
                <div class="media-meta">
                    <h3 id="videoTitle">Media Title</h3>
                    <div class="meta-tags">
                        <span class="tag-pill" id="platformTag"><i class="fa-solid fa-globe"></i> Detected</span>
                        <span class="tag-pill" id="durationTag"><i class="fa-regular fa-clock"></i> Ready</span>
                        <span class="tag-pill"><i class="fa-solid fa-circle-check" style="color:var(--success);"></i> High Speed CDN</span>
                    </div>
                    <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.4;">
                        Live stream ready. Apna format aur quality select karke download karein:
                    </p>
                </div>
            </div>

            <div class="format-nav">
                <button class="f-btn active" onclick="switchFormatTab('video', this)"><i class="fa-solid fa-film"></i> Video Streams (MP4)</button>
                <button class="f-btn" onclick="switchFormatTab('audio', this)"><i class="fa-solid fa-headphones"></i> Audio Extracts (MP3)</button>
            </div>

            <div class="quality-grid" id="videoFormats"></div>
            <div class="quality-grid" id="audioFormats" style="display: none;"></div>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 MediaStudio • High Speed Multi-Stream Downloader</p>
    </footer>

    <script>
        function extractYouTubeID(url) {
            const regExp = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=|shorts\/)|youtu\.be\/)([^"&?\/\s]{11})/i;
            const match = url.match(regExp);
            return (match && match) ? match : null;
        }

        function extractInstagramID(url) {
            const regExp = /(?:instagram\.com\/(?:p|reel|reels)\/)([^/?#&]+)/i;
            const match = url.match(regExp);
            return (match && match) ? match : null;
        }

        async function processDownloadRequest() {
            const url = document.getElementById('videoUrl').value.trim();
            const loader = document.getElementById('loader');
            const resultContainer = document.getElementById('resultContainer');
            const playerWrapper = document.getElementById('playerWrapper');
            const videoFormatsDiv = document.getElementById('videoFormats');
            const audioFormatsDiv = document.getElementById('audioFormats');

            if (!url) {
                alert('Kripya video ka valid link paste karein!');
                return;
            }

            loader.style.display = 'block';
            resultContainer.style.display = 'none';
            playerWrapper.innerHTML = '';
            playerWrapper.classList.remove('reel-mode');

            const ytId = extractYouTubeID(url);
            const igId = extractInstagramID(url);

            if (ytId) {
                if (url.includes('/shorts/')) playerWrapper.classList.add('reel-mode');
                playerWrapper.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${ytId}?autoplay=1&rel=0" allowfullscreen></iframe>`;
            } else if (igId) {
                playerWrapper.classList.add('reel-mode');
                playerWrapper.innerHTML = `<iframe src="https://www.instagram.com/p/${igId}/embed/" frameborder="0" scrolling="no"></iframe>`;
            } else if (url.includes('facebook.com') || url.includes('fb.watch')) {
                const encoded = encodeURIComponent(url);
                playerWrapper.innerHTML = `<iframe src="https://www.facebook.com/plugins/video.php?href=${encoded}&show_text=false&autoplay=true" allowfullscreen></iframe>`;
            }

            try {
                const response = await fetch('/api/get-info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (!data.success) {
                    // Fallback to client-side direct resolver if server times out
                    handleFallbackDownload(url, ytId);
                    return;
                }

                if (!playerWrapper.innerHTML.trim() && data.thumbnail) {
                    playerWrapper.innerHTML = `<img src="${data.thumbnail}" alt="Thumbnail">`;
                }

                document.getElementById('videoTitle').innerText = data.title;
                document.getElementById('platformTag').innerHTML = `<i class="fa-solid fa-circle-check" style="color:var(--success);"></i> ${data.platform}`;
                document.getElementById('durationTag').innerHTML = `<i class="fa-regular fa-clock"></i> ${data.duration}`;

                // Video Formats (144p to 2K)
                videoFormatsDiv.innerHTML = '';
                if (data.videos && data.videos.length > 0) {
                    data.videos.forEach(v => {
                        let resNum = parseInt(v.resolution.replace('p', '')) || 0;
                        let badgeClass = 'badge-res';
                        if (resNum >= 1440) badgeClass += ' uhd';
                        else if (resNum >= 1080) badgeClass += ' fhd';
                        else if (resNum >= 720) badgeClass += ' hd';

                        const div = document.createElement('div');
                        div.className = 'q-card';
                        div.innerHTML = `
                            <div class="q-left">
                                <span class="${badgeClass}">${v.resolution}</span>
                                <div><strong>${v.resolution} MP4</strong> <span style="color: var(--text-muted); font-size: 0.82rem;">• Direct Stream</span></div>
                            </div>
                            <a href="${v.download_url}" target="_blank" rel="noopener noreferrer" class="btn-dl">
                                <i class="fa-solid fa-download"></i> Save File
                            </a>
                        `;
                        videoFormatsDiv.appendChild(div);
                    });
                }

                // Audio Formats
                audioFormatsDiv.innerHTML = '';
                if (data.audios && data.audios.length > 0) {
                    data.audios.forEach(a => {
                        const div = document.createElement('div');
                        div.className = 'q-card';
                        div.innerHTML = `
                            <div class="q-left">
                                <span class="badge-res uhd">${a.abr} kbps</span>
                                <div><strong>Audio (MP3)</strong> <span style="color: var(--text-muted); font-size: 0.82rem;">• Clean Audio Stream</span></div>
                            </div>
                            <a href="${a.download_url}" target="_blank" rel="noopener noreferrer" class="btn-dl">
                                <i class="fa-solid fa-download"></i> Save MP3
                            </a>
                        `;
                        audioFormatsDiv.appendChild(div);
                    });
                }

                loader.style.display = 'none';
                resultContainer.style.display = 'block';

            } catch (err) {
                handleFallbackDownload(url, ytId);
            }
        }

        function handleFallbackDownload(url, ytId) {
            const loader = document.getElementById('loader');
            const resultContainer = document.getElementById('resultContainer');
            const videoFormatsDiv = document.getElementById('videoFormats');
            const audioFormatsDiv = document.getElementById('audioFormats');

            loader.style.display = 'none';
            resultContainer.style.display = 'block';

            document.getElementById('videoTitle').innerText = "Direct Stream Link Ready";
            document.getElementById('platformTag').innerHTML = `<i class="fa-solid fa-shield-halved" style="color:var(--success);"></i> High Speed Engine`;

            let directDownloadLink = "https://10downloader.com/download?v=" + encodeURIComponent(url);
            if (url.includes('instagram.com')) {
                directDownloadLink = "https://snapinsta.app/result?url=" + encodeURIComponent(url);
            } else if (url.includes('facebook.com')) {
                directDownloadLink = "https://fdown.net/download.php?url=" + encodeURIComponent(url);
            }

            videoFormatsDiv.innerHTML = `
                <div class="q-card">
                    <div class="q-left">
                        <span class="badge-res uhd">HD / 2K</span>
                        <div><strong>Best Available Quality (MP4)</strong></div>
                    </div>
                    <a href="${directDownloadLink}" target="_blank" class="btn-dl">
                        <i class="fa-solid fa-download"></i> Direct Download
                    </a>
                </div>
            `;

            audioFormatsDiv.innerHTML = `
                <div class="q-card">
                    <div class="q-left">
                        <span class="badge-res uhd">320 kbps</span>
                        <div><strong>High Quality MP3 Audio</strong></div>
                    </div>
                    <a href="${directDownloadLink}" target="_blank" class="btn-dl">
                        <i class="fa-solid fa-download"></i> Direct Download MP3
                    </a>
                </div>
            `;
        }

        function switchFormatTab(tabType, element) {
            document.querySelectorAll('.f-btn').forEach(btn => btn.classList.remove('active'));
            element.classList.add('active');

            const videoDiv = document.getElementById('videoFormats');
            const audioDiv = document.getElementById('audioFormats');

            if (tabType === 'video') {
                videoDiv.style.display = 'flex';
                audioDiv.style.display = 'none';
            } else {
                videoDiv.style.display = 'none';
                audioDiv.style.display = 'flex';
            }
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# INVIDIOUS HIGH-SPEED GLOBAL PROXY NETWORK (BYPASSES RENDER IP BLOCK)
# ==============================================================================
INVIDIOUS_NODES = [
    "https://invidious.nerdvpn.de",
    "https://inv.tux.pizza",
    "https://yewtu.be",
    "https://vid.puffyan.us",
    "https://invidious.drgns.space"
]

def fetch_youtube_via_invidious(yt_id):
    for node in INVIDIOUS_NODES:
        try:
            api_url = f"{node}/api/v1/videos/{yt_id}"
            res = requests.get(api_url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                videos = []
                audios = []
                seen_res = set()

                # Extract Progressive Video Streams (720p, 360p, 480p)
                for item in data.get('formatStreams', []):
                    res_label = item.get('qualityLabel') or f"{item.get('resolution')}p"
                    if res_label and res_label not in seen_res:
                        seen_res.add(res_label)
                        videos.append({
                            'resolution': res_label,
                            'download_url': item.get('url')
                        })

                # Extract Adaptive High-Res (1080p, 1440p)
                for item in data.get('adaptiveFormats', []):
                    q_label = item.get('qualityLabel')
                    if q_label and q_label not in seen_res and 'video' in item.get('type', ''):
                        seen_res.add(q_label)
                        videos.append({
                            'resolution': q_label,
                            'download_url': item.get('url')
                        })
                    elif 'audio' in item.get('type', ''):
                        audios.append({
                            'abr': 192,
                            'download_url': item.get('url')
                        })

                if not audios and videos:
                    audios.append({'abr': 192, 'download_url': videos[0]['download_url']})

                return {
                    'success': True,
                    'title': data.get('title', 'YouTube Video'),
                    'thumbnail': f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg",
                    'duration': f"{int(data.get('lengthSeconds', 0)) // 60}:{int(data.get('lengthSeconds', 0)) % 60:02d}",
                    'platform': 'YouTube',
                    'videos': videos,
                    'audios': audios
                }
        except Exception:
            continue
    return None

# ==============================================================================
# FLASK ROUTES
# ==============================================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get-info', methods=['POST'])
def extract_media_info():
    data = request.get_json() or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'success': False, 'error': 'URL missing'}), 400

    # Extract YouTube Video ID
    yt_match = re.search(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=|shorts\/)|youtu\.be\/)([^"&?\/\s]{11})', url)
    
    if yt_match:
        yt_id = yt_match.group(1)
        # Use Invidious global network (Bypasses Render bot-check)
        inv_data = fetch_youtube_via_invidious(yt_id)
        if inv_data:
            return jsonify(inv_data)

    # Universal Stream Fallback (Instagram / Facebook / Direct)
    return jsonify({
        'success': True,
        'title': 'Media Stream Ready',
        'thumbnail': '',
        'duration': 'Live Stream',
        'platform': 'Universal Extractor',
        'videos': [
            {'resolution': '1080p', 'download_url': f"https://10downloader.com/download?v={urllib.parse.quote(url)}"},
            {'resolution': '720p', 'download_url': f"https://10downloader.com/download?v={urllib.parse.quote(url)}"},
            {'resolution': '480p', 'download_url': f"https://10downloader.com/download?v={urllib.parse.quote(url)}"}
        ],
        'audios': [
            {'abr': 320, 'download_url': f"https://10downloader.com/download?v={urllib.parse.quote(url)}"}
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

