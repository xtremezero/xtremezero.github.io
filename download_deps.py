import urllib.request
import re
import os
import ssl
import sys

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# SSL context
ctx = ssl._create_unverified_context()

def fetch_url_bytes(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_url_text(url):
    data = fetch_url_bytes(url)
    if data:
        return data.decode('utf-8', errors='ignore')
    return None

def download_file(url, filepath):
    print(f"Downloading {url} to {filepath}...")
    data = fetch_url_bytes(url)
    if data:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"  Successfully saved {filepath} ({len(data)} bytes)")
        return True
    else:
        print(f"  Failed to download {url}")
        return False

def main():
    lib_dir = "lib"
    fonts_dir = os.path.join(lib_dir, "fonts")
    
    # 1. Download JS Libraries
    js_libs = {
        "https://cdn.tailwindcss.com": os.path.join(lib_dir, "tailwind.min.js"),
        "https://unpkg.com/react@18/umd/react.production.min.js": os.path.join(lib_dir, "react.production.min.js"),
        "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js": os.path.join(lib_dir, "react-dom.production.min.js"),
        "https://unpkg.com/@babel/standalone/babel.min.js": os.path.join(lib_dir, "babel.min.js")
    }
    
    print("--- DOWNLOADING JS LIBRARIES ---")
    for url, path in js_libs.items():
        download_file(url, path)
        
    # 2. Download Google Fonts CSS and Font files
    print("\n--- DOWNLOADING GOOGLE FONTS ---")
    fonts_css_url = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Orbitron:wght@500;600;700;800;900&family=Rajdhani:wght@500;600;700&display=swap"
    
    css_content = fetch_url_text(fonts_css_url)
    if not css_content:
        print("Failed to fetch Google Fonts stylesheet CSS.")
        sys.exit(1)
        
    # Find all font URLs in CSS
    # e.g., src: url(https://fonts.gstatic.com/s/inter/...woff2) format('woff2');
    font_urls = re.findall(r'url\((https://[^\)]+\.woff2)\)', css_content)
    print(f"Found {len(font_urls)} font files to download.")
    
    os.makedirs(fonts_dir, exist_ok=True)
    
    downloaded_fonts = {}
    for url in set(font_urls):
        filename = url.split('/')[-1]
        local_path = os.path.join(fonts_dir, filename)
        # Download the file
        if download_file(url, local_path):
            # Map url to local reference
            downloaded_fonts[url] = f"fonts/{filename}"
            
    # Rewrite CSS url() references
    print("\nRewriting fonts CSS stylesheet links...")
    rewritten_css = css_content
    for url, local_ref in downloaded_fonts.items():
        # Escape any regex special characters in URL
        escaped_url = re.escape(url)
        rewritten_css = re.sub(escaped_url, local_ref, rewritten_css)
        
    fonts_css_path = os.path.join(lib_dir, "fonts.css")
    with open(fonts_css_path, "w", encoding="utf-8") as f:
        f.write(rewritten_css)
    print(f"Successfully saved rewritten CSS to {fonts_css_path}")
    print("Done!")

if __name__ == "__main__":
    main()
