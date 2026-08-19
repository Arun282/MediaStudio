import os
import urllib.parse
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==============================================================================
# FULL NEW THEME & CLIENT-SIDE RESOLVER (HTML + CSS + JS)
# ==============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Download Karo - YouTube, Reels & FB Downloader</title>
    
    <!-- Google Fonts & Font Awesome Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #10b981;
            --primary-glow: rgba(16, 185, 129, 0.35);
            --accent-indigo: #6366f1;
            --bg-dark: #07090e;
            --card-bg: #111625;
            --card-border: #1f293d;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --yt-color: #ff0000;
            --ig-color: #e1306c;
            --fb-color: #1877f2;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', 'Poppins', sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; }

        /* Navbar Header */
        header {
            background: rgba(17, 22, 37, 0.85);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--card-border);
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 1.4rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #fff;
            text-decoration: none;
            letter-spacing: -0.5px;
        }
        .logo i { color: var(--primary); text-shadow: 0 0 15px var(--primary-glow); }
        .logo span { color: var(--primary); }

        main {
            flex: 1;
            max-width: 860px;
            width: 100%;
            margin: 1.8rem auto;
            padding: 0 1rem;
        }

        /* Hero */
        .hero { text-align: center; margin-bottom: 2rem; }
        .hero h1 {
            font-size: 2.3rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #ffffff, #a7f3d0, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }
        .hero p { color: var(--text-muted); font-size: 0.95rem; }

        /* Platform Badges */
        .platform-badges {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin: 1.3rem 0;
            flex-wrap: wrap;
        }
        .badge {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 7px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        .badge.yt i { color: var(--yt-color); }
        .badge.ig i { color: var(--ig-color); }
        .badge.fb i { color: var(--fb-color); }

        /* Search Input Box */
        .search-box {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.2rem;
            box-shadow: 0 12px 35px -10px rgba(0, 0, 0, 0.6);
        }
        .input-wrapper { display: flex; gap: 10px; }
        .input-wrapper input {
            flex: 1;
            background: #090d16;
            border: 1px solid var(--card-border);
            padding: 1rem 1.2rem;
            border-radius: 12px;
            color: #fff;
            font-size: 1rem;
            outline: none;
            transition: all 0.3s;
        }
        .input-wrapper input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 15px var(--primary-glow);
        }

        .btn-fetch {
            background: linear-gradient(135deg, #10b981, #059669);
            color: #fff;
            border: none;
            padding: 0 1.8rem;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px var(--primary-glow);
            white-space: nowrap;
        }
        .btn-fetch:hover { transform: translateY(-2px); }

        /* Result Section */
        .result-container {
            display: none;
            margin-top: 1.8rem;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 1.6rem;
            animation: fadeIn 0.35s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Live Preview Player */
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
        .video-player-box iframe, .video-player-box video {
            width: 100%; height: 100%; min-height: 180px; border: none; border-radius: 12px;
        }
        .video-player-box.reel-mode iframe { min-height: 380px; }

        .media-meta h3 { font-size: 1.15rem; margin-bottom: 0.5rem; line-height: 1.4; color: #fff; }
        .meta-tags { display: flex; gap: 8px; margin-bottom: 0.8rem; flex-wrap: wrap; }
        .tag-pill {
            background: #1e293b; color: var(--text-muted); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 6px;
        }

        /* Format Tabs */
        .format-nav {
            display: flex; gap: 10px; margin-bottom: 1.2rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.8rem;
        }
        .f-btn {
            background: transparent; border: 1px solid var(--card-border); color: var(--text-muted); padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600; display: flex; align-items: center; gap: 8px;
        }
        .f-btn.active {
            background: var(--primary); color: #000; border-color: var(--primary); font-weight: 700;
        }

        /* Quality Cards */
        .quality-grid { display: flex; flex-direction: column; gap: 10px; }
        .q-card {
            display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #090d16; border: 1px solid var(--card-border); border-radius: 12px;
        }
        .q-left { display: flex; align-items: center; gap: 12px; }

        .badge-res { padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; background: #334155; }
        .badge-res.uhd { background: #7c3aed; color: #fff; }
        .badge-res.fhd { background: #0284c7; color: #fff; }
        .badge-res.hd { background: #059669; color: #fff; }

        .btn-dl {
            background: linear-gradient(135deg, #10b981, #059669);
            color: #fff;
            padding: 8px 20px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 700;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 12px var(--primary-glow);
            transition: all 0.2s;
        }
        .btn-dl:hover { transform: scale(1.03); background: #059669; }

        footer { text-align: center; padding: 1.5rem; color: var(--text-muted); font-size: 0.85rem; border-top: 1px solid var(--card-border); margin-top: auto; }
        @media (max-width: 720px) { .preview-layout { grid-template-columns: 1fr; } .input-wrapper { flex-direction: column; } }
    </style>
</head>
<body>

    <header>
        <a href="#" class="logo">
            <i class="fa-solid fa-cloud-arrow-down"></i> Video<span>Download</span>Karo
        </a>
    </header>

    <main>
        <section class="hero">
            <h1>Video Download Karo</h1>
            <p>YouTube Videos, Shorts, Instagram Reels & Facebook Clips 144p se 2K tak Download Karein</p>
            
            <div class="platform-badges">
                <div class="badge yt"><i class="fa-brands fa-youtube"></i> YouTube & Shorts</div>
                <div class="badge ig"><i class="fa-brands fa-instagram"></i> Instagram Reels</div>
                <div class="badge fb"><i class="fa-brands fa-facebook"></i> Facebook Video</div>
            </div>
        </section>

        <!-- Search Input -->
        <section class="search-box">
            <div class="input-wrapper">
                <input type="text" id="videoUrl" placeholder="Video ya Reel ka link yahan paste karein...">
                <button class="btn-fetch" onclick="processInstantMedia()">
                    <i class="fa-solid fa-bolt"></i> Download Links
                </button>
            </div>
        </section>

        <!-- Result Box -->
        <section class="result-container" id="resultContainer">
            
            <div class="preview-layout">
                <!-- EXACT Live Player Container -->
                <div class="video-player-box" id="playerWrapper"></div>

                <!-- Media Details -->
                <div class="media-meta">
                    <h3 id="videoTitle">Live Media Ready</h3>
                    
                    <div class="meta-tags">
                        <span class="tag-pill" id="platformTag"><i class="fa-solid fa-globe"></i> Verified</span>
                        <span class="tag-pill"><i class="fa-solid fa-bolt" style="color:var(--primary);"></i> Super Fast Stream</span>
                        <span class="tag-pill"><i class="fa-solid fa-circle-check" style="color:var(--primary);"></i> 100% Working</span>
                    </div>

                    <p style="color: var(--text-muted); font-size: 0.88rem; line-height: 1.4;">
                        Aapke video ka live preview upar chal raha hai. Neeche se quality select karke <strong>Download File</strong> par click karein:
                    </p>
                </div>
            </div>

            <!-- Format Tabs -->
            <div class="format-nav">
                <button class="f-btn active" onclick="switchFormatTab('video', this)"><i class="fa-solid fa-film"></i> Video (144p - 2K)</button>
                <button class="f-btn" onclick="switchFormatTab('audio', this)"><i class="fa-solid fa-headphones"></i> Audio (MP3)</button>
            </div>

            <!-- Video Formats List -->
            <div class="quality-grid" id="videoFormats"></div>

            <!-- Audio Formats List -->
            <div class="quality-grid" id="audioFormats" style="display: none;"></div>

        </section>
    </main>

    <footer>
        <p>&copy; 2026 Video Download Karo • All Rights Reserved</p>
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

        function processInstantMedia() {
            const url = document.getElementById('videoUrl').value.trim();
            const resultContainer = document.getElementById('resultContainer');
            const playerWrapper = document.getElementById('playerWrapper');
            const videoFormatsDiv = document.getElementById('videoFormats');
            const audioFormatsDiv = document.getElementById('audioFormats');
            const platformTag = document.getElementById('platformTag');
            const videoTitle = document.getElementById('videoTitle');

            if (!url) {
                alert('Kripya video ka link paste karein!');
                return;
            }

            playerWrapper.innerHTML = '';
            playerWrapper.classList.remove('reel-mode');

            const ytId = extractYouTubeID(url);
            const igId = extractInstagramID(url);

            let downloadUrlBase = "";

            if (ytId) {
                const isShorts = url.includes('/shorts/');
                if (isShorts) playerWrapper.classList.add('reel-mode');
                
                playerWrapper.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${ytId}?autoplay=1&rel=0" allowfullscreen></iframe>`;
                platformTag.innerHTML = `<i class="fa-brands fa-youtube" style="color:var(--yt-color);"></i> YouTube ${isShorts ? 'Shorts' : 'Video'}`;
                videoTitle.innerText = `YouTube Video Stream (${ytId})`;
                downloadUrlBase = "https://10downloader.com/download?v=" + encodeURIComponent(url);
            } 
            else if (igId) {
                playerWrapper.classList.add('reel-mode');
                playerWrapper.innerHTML = `<iframe src="https://www.instagram.com/p/${igId}/embed/" frameborder="0" scrolling="no"></iframe>`;
                platformTag.innerHTML = `<i class="fa-brands fa-instagram" style="color:var(--ig-color);"></i> Instagram Reel`;
                videoTitle.innerText = `Instagram Reel Media (${igId})`;
                downloadUrlBase = "https://snapinsta.app/result?url=" + encodeURIComponent(url);
            } 
            else if (url.includes('facebook.com') || url.includes('fb.watch')) {
                const encoded = encodeURIComponent(url);
                playerWrapper.innerHTML = `<iframe src="https://www.facebook.com/plugins/video.php?href=${encoded}&show_text=false&autoplay=true" allowfullscreen></iframe>`;
                platformTag.innerHTML = `<i class="fa-brands fa-facebook" style="color:var(--fb-color);"></i> Facebook Video`;
                videoTitle.innerText = `Facebook Video Stream`;
                downloadUrlBase = "https://fdown.net/download.php?url=" + encodeURIComponent(url);
            } 
            else {
                playerWrapper.innerHTML = `<video controls autoplay src="${url}" style="width:100%; height:100%;"></video>`;
                platformTag.innerHTML = `<i class="fa-solid fa-globe"></i> Web Media`;
                videoTitle.innerText = `Direct Media Video`;
                downloadUrlBase = url;
            }

            // Render 144p to 2K Video Cards
            const videoResolutions = [
                { res: '2K (1440p)', tag: 'uhd', label: 'Quad HD Quality' },
                { res: '1080p', tag: 'fhd', label: 'Full HD Quality' },
                { res: '720p', tag: 'hd', label: 'High Definition' },
                { res: '480p', tag: '', label: 'Standard (SD)' },
                { res: '360p', tag: '', label: 'Medium Quality' },
                { res: '240p', tag: '', label: 'Low Resolution' },
                { res: '144p', tag: '', label: 'Data Saver' }
            ];

            videoFormatsDiv.innerHTML = '';
            videoResolutions.forEach(item => {
                const div = document.createElement('div');
                div.className = 'q-card';
                div.innerHTML = `
                    <div class="q-left">
                        <span class="badge-res ${item.tag}">${item.res}</span>
                        <div><strong>${item.res} MP4</strong> <span style="color: var(--text-muted); font-size: 0.82rem;">• ${item.label}</span></div>
                    </div>
                    <a href="${downloadUrlBase}" target="_blank" rel="noopener noreferrer" class="btn-dl">
                        <i class="fa-solid fa-download"></i> Download File
                    </a>
                `;
                videoFormatsDiv.appendChild(div);
            });

            // Render MP3 Audio Cards
            const audioBitrates = [
                { abr: '320 kbps', label: 'Ultra High Quality (MP3)' },
                { abr: '192 kbps', label: 'High Quality Audio' },
                { abr: '128 kbps', label: 'Standard Audio' }
            ];

            audioFormatsDiv.innerHTML = '';
            audioBitrates.forEach(item => {
                const div = document.createElement('div');
                div.className = 'q-card';
                div.innerHTML = `
                    <div class="q-left">
                        <span class="badge-res uhd">${item.abr}</span>
                        <div><strong>Audio (MP3)</strong> <span style="color: var(--text-muted); font-size: 0.82rem;">• ${item.label}</span></div>
                    </div>
                    <a href="${downloadUrlBase}" target="_blank" rel="noopener noreferrer" class="btn-dl">
                        <i class="fa-solid fa-download"></i> Download MP3
                    </a>
                `;
                audioFormatsDiv.appendChild(div);
            });

            resultContainer.style.display = 'block';
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
# FLASK SERVER ROUTE
# ==============================================================================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Video Download Karo is live on port: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

