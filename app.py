import os
import shutil
import tempfile
import re
from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>YouTube to MP3 Converter</title>
            <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IjI1IiBmaWxsPSIjMTcxQjJGIi8+PHBvbHlnb24gcG9pbnRzPSI0MCwzMCA0MCw3MCA3NSw1MCIgZmlsbD0iI0JEQjVENTIiLz48L3N2Zz4=">
            <style>
                body {
                    background-color: #0A0D1A;
                    color: #A5AEC4;
                    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .card {
                    background: #171B2F;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
                    width: 90%;
                    max-width: 480px;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                .logo-container {
                    width: 140px;
                    height: 140px;
                    background: linear-gradient(135deg, #18122B 0%, #0B0914 100%);
                    border-radius: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 35px;
                    box-shadow: inset 0 2px 5px rgba(255,255,255,0.05), 0 10px 30px rgba(0,0,0,0.5);
                }
                .play-triangle {
                    width: 0;
                    height: 0;
                    border-top: 25px solid transparent;
                    border-bottom: 25px solid transparent;
                    border-left: 44px solid #8A2BE2;
                    background: linear-gradient(to right, #A044FF, #D444FF);
                    -webkit-background-clip: padding-box;
                    background-clip: padding-box;
                    margin-left: 10px;
                    filter: drop-shadow(0 4px 15px rgba(160, 68, 255, 0.6));
                }
                .description {
                    font-size: 14px;
                    color: #707993;
                    margin-bottom: 25px;
                    font-weight: 500;
                }
                .toggle-container {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 12px;
                    margin-bottom: 25px;
                    font-size: 14px;
                    color: #A5AEC4;
                }
                .switch {
                    position: relative;
                    display: inline-block;
                    width: 48px;
                    height: 24px;
                }
                .switch input { 
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                .slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background-color: #24283D;
                    transition: .3s;
                    border-radius: 24px;
                    border: 1px solid #29304E;
                }
                .slider:before {
                    position: absolute;
                    content: "";
                    height: 16px;
                    width: 16px;
                    left: 3px;
                    bottom: 3px;
                    background-color: #707993;
                    transition: .3s;
                    border-radius: 50%;
                }
                input:checked + .slider {
                    background-color: #5D5299;
                    border-color: #6C5FA9;
                }
                input:checked + .slider:before {
                    transform: translateX(24px);
                    background-color: #FFFFFF;
                }
                .form-inline {
                    display: flex;
                    width: 100%;
                    gap: 12px;
                    align-items: center;
                }
                input[type="text"] {
                    flex: 1;
                    padding: 14px 18px;
                    border: 1px solid #29304E;
                    border-radius: 30px;
                    font-size: 14px;
                    outline: none;
                    background: #121526;
                    color: #FFFFFF;
                }
                button.submit-btn {
                    padding: 14px 28px;
                    background-color: #5D5299;
                    color: #A5AEC4;
                    border: none;
                    border-radius: 30px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                button.submit-btn:hover {
                    background-color: #6C5FA9;
                    color: #FFFFFF;
                }
                button.submit-btn:disabled {
                    background-color: #24283D;
                    color: #485273;
                    cursor: not-allowed;
                }
                #statusMessage {
                    margin-top: 20px;
                    font-size: 13px;
                    color: #707993;
                    min-height: 18px;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo-container">
                    <div class="play-triangle"></div>
                </div>
                <div class="description">Paste a YouTube URL and download the audio as MP3</div>
                
                <div class="toggle-container">
                    <span>Single Video</span>
                    <label class="switch">
                        <input type="checkbox" id="playlistToggle">
                        <span class="slider"></span>
                    </label>
                    <span>Entire Playlist</span>
                </div>

                <form id="downloadForm" class="form-inline">
                    <input type="text" id="url" name="url" placeholder="https://youtube.com..." required autocomplete="off">
                    <button type="submit" id="submitBtn" class="submit-btn">Download</button>
                </form>
                <div id="statusMessage"></div>
            </div>

            <script>
                document.getElementById('downloadForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const urlInput = document.getElementById('url');
                    const isPlaylist = document.getElementById('playlistToggle').checked;
                    const btn = document.getElementById('submitBtn');
                    const status = document.getElementById('statusMessage');
                    
                    btn.disabled = true;
                    btn.innerText = 'Processing...';
                    status.innerText = isPlaylist ? 'Ripping full playlist... This may take a while.' : 'Ripping audio stream...';

                    try {
                        const response = await fetch('/download', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                url: urlInput.value,
                                download_playlist: isPlaylist
                            })
                        });

                        if (!response.ok) {
                            const errData = await response.json();
                            throw new Error(errData.error || 'Server error occurred.');
                        }

                        status.innerText = 'Sending file to browser...';
                        
                        const contentDisposition = response.headers.get('Content-Disposition');
                        let filename = isPlaylist ? 'playlist.zip' : 'audio.mp3';
                        if (contentDisposition && contentDisposition.includes('filename=')) {
                            filename = contentDisposition.split('filename=')[1].replace(/["']/g, '');
                        }

                        const blob = await response.blob();
                        const downloadUrl = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = downloadUrl;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(downloadUrl);

                        status.innerText = 'Download complete!';
                        urlInput.value = '';
                    } catch (err) {
                        status.innerText = 'Error: ' + err.message;
                    } finally {
                        btn.disabled = false;
                        btn.innerText = 'Download';
                    }
                });
            </script>
        </body>
        </html>
    ''')

@app.route('/favicon.ico')
def favicon():
    svg_data = '<svg xmlns="http://w3.org" viewBox="0 0 100 100"><rect width="100" height="100" rx="25" fill="#171B2F"/><polygon points="40,30 40,70 75,50" fill="#BDB5D5"/></svg>'
    return svg_data, 200, {'Content-Type': 'image/svg+xml'}


@app.route('/download', methods=['POST'])
def download_audio():
    data = request.get_json()
    video_url = data.get('url') if data else None
    download_playlist = data.get('download_playlist', False) if data else False

    if not video_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if download_playlist:
        with tempfile.TemporaryDirectory() as temp_batch_dir:
            ydl_opts = {
                'noplaylist': False,
                'max_downloads': 20,  # Limits playlist to the first 20 songs
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_batch_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=True)
                    playlist_title = info_dict.get('title', 'playlist')
                
                clean_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title)
                zip_base_name = os.path.join(DOWNLOAD_DIR, clean_title)
                archive_path = shutil.make_archive(zip_base_name, 'zip', temp_batch_dir)
                
                return send_file(
                    archive_path,
                    as_attachment=True,
                    download_name=f"{clean_title}.zip"
                )
            except Exception as e:
                # Catch the specific max downloads stop or generic errors gracefully
                if "Max downloads reached" in str(e) or temp_batch_dir:
                    playlist_title = "playlist_limited"
                    clean_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title)
                    zip_base_name = os.path.join(DOWNLOAD_DIR, clean_title)
                    archive_path = shutil.make_archive(zip_base_name, 'zip', temp_batch_dir)
                    return send_file(
                        archive_path,
                        as_attachment=True,
                        download_name=f"{clean_title}.zip"
                    )
                return jsonify({"error": str(e)}), 500
    else:
        ydl_opts = {
            'noplaylist': True,
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                temp_filename = ydl.prepare_filename(info_dict)
                mp3_filepath = os.path.splitext(temp_filename)[0] + '.mp3'
            
            return send_file(
                mp3_filepath, 
                as_attachment=True, 
                download_name=os.path.basename(mp3_filepath)
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
