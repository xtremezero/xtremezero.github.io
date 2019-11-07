import urllib.request
import re
import json
import ssl
import sys
import time
import os
from html import unescape

# Ensure the terminal handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DATA_FILE = "data.json"

DEFAULT_ABOUT = {
    "name": "XtremeZero",
    "avatar": "https://img.itch.zone/aW1nLzIwNjUxMjUyLnBuZw==/original/KUsoYC.png",
    "bio": "",
    "email": "",
    "skills": []
}

DEFAULT_LINKS = [
    {"id": "itch", "title": "itch.io Profile", "url": "https://xtremezero.itch.io", "category": "PORTFOLIO", "clicks": 0},
    {"id": "website", "title": "Official Website", "url": "https://xtremezero.xyz", "category": "HOMEPAGE", "clicks": 0},
    {"id": "github", "title": "GitHub Profile", "url": "https://github.com/xtremezero", "category": "CODE", "clicks": 0},
    {"id": "steam", "title": "Steam Store", "url": "https://steamcommunity.com/id/mohammedzero43", "category": "STOREFRONT", "clicks": 0},
    {"id": "gog", "title": "GOG Profile", "url": "https://www.gog.com/u/xtremezero", "category": "STOREFRONT", "clicks": 0},
    {"id": "x", "title": "X / Twitter", "url": "https://x.com/xtremezero_", "category": "SOCIAL", "clicks": 0},
    {"id": "instagram", "title": "Instagram Profile", "url": "https://instagram.com/xtremezero_", "category": "SOCIAL", "clicks": 0},
    {"id": "reddit", "title": "Reddit Profile", "url": "https://www.reddit.com/user/xtremezero_", "category": "SOCIAL", "clicks": 0},
    {"id": "youtube", "title": "YouTube Channel", "url": "https://youtube.com/@xtremezero", "category": "BROADCAST", "clicks": 0},
    {"id": "gamejolt", "title": "Game Jolt", "url": "https://gamejolt.com/@xtremezero", "category": "PORTFOLIO", "clicks": 0},
    {"id": "discord", "title": "Discord: @xtremezeroxz", "url": "https://discord.com", "category": "COMMUNITY", "clicks": 0},
    {"id": "twitch", "title": "Twitch Channel", "url": "https://twitch.tv/xtremezero_", "category": "BROADCAST", "clicks": 0}
]

DEFAULT_NEWS = [
    {
        "id": "beat-slicer-update",
        "title": "BEAT//SLICER VERSION 1.2 OUT NOW",
        "category": "UPDATE",
        "date": "2026-07-09",
        "image": "https://img.itch.zone/aW1nLzI4MjYzMDM2LmdpZg==/original/6B74sl.gif",
        "summary": "New stability fixes and 2 new synthwave levels added directly to the tracklist. Go slash some neon beats!",
        "likes": 124
    },
    {
        "id": "archers-hitteen-devlog",
        "title": "رماة حطين: MULTIPLAYER PROTOTYPE SHOWN",
        "category": "DEVLOG",
        "date": "2026-07-08",
        "image": "https://img.itch.zone/aW1nLzIxMTUxOTc4LnBuZw==/original/17KuTM.png",
        "summary": "Unveiling cooperative defense prototype. Test your archery skills alongside friends to hold the water wells against incoming forces.",
        "likes": 345
    },
    {
        "id": "godot-plugins-v4",
        "title": "GODOT PLUGINS NOW COMPATIBLE WITH GODOT 4.3",
        "category": "TOOLS",
        "date": "2026-07-05",
        "image": "https://img.itch.zone/aW1nLzY1NTc2NjcucG5n/315x250%23c/WkMIkq.png",
        "summary": "The Godot CSG Exporter and Selection Tools have been fully rewritten and compiled to run on Godot 4.3 stable versions.",
        "likes": 89
    }
]

def fetch_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def _parse_info_panel_row(html, label):
    """Extract a value from a game_info_panel_widget table row by label."""
    pattern = r'<tr>\s*<td>' + re.escape(label) + r'</td>\s*<td>(.*?)</td>\s*</tr>'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def _parse_date_from_abbr(html_fragment):
    """Extract an ISO date (YYYY-MM-DD) from an <abbr title="..."> inside an HTML fragment."""
    abbr_match = re.search(r'<abbr\s+title="([^"]+)"', html_fragment)
    if abbr_match:
        raw = abbr_match.group(1).strip()
        # Formats: "10 July 2026 @ 17:25 UTC" or "2026-07-10 17:10:03"
        for fmt in ("%d %B %Y @ %H:%M %Z", "%d %B %Y @ %H:%M UTC", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                from datetime import datetime
                dt = datetime.strptime(raw.replace(" UTC", "").strip(), fmt.replace(" %Z", "").replace(" UTC", ""))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""

def parse_subpage(url):
    print(f"  Scraping subpage: {url} ...", flush=True)
    html = fetch_url(url)
    if not html:
        return {
            "banner": "", "screenshots": [], "longDescription": "",
            "price": "FREE", "status": "", "publishedDate": "",
            "updatedDate": "", "releaseDate": "", "madeWith": "",
            "tags": [], "ratingValue": 0, "ratingCount": 0, "hasDevlog": False
        }
    
    # 1. Background image (large banner)
    banner_match = re.search(r'background-image:\s*url\((["\']?)(https://img\.itch\.zone/[^)]+?)\1\)', html)
    banner = banner_match.group(2) if banner_match else ""
    
    # 2. Screenshots
    screenshot_list_match = re.search(r'<div[^>]*class="screenshot_list"[^>]*>(.*?)</div>', html, re.DOTALL)
    screenshots = []
    if screenshot_list_match:
        screenshot_list_html = screenshot_list_match.group(1)
        screenshots = re.findall(r'<a[^>]*href="([^"]+)"', screenshot_list_html)
    else:
        screenshots = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*screenshot[^"]*"', html)
    
    # 3. Full description
    desc_match = re.search(r'<div[^>]*class="formatted_description[^"]*"[^>]*>(.*?)</div>\s*<div[^>]*class="[^"]*game_info_panel', html, re.DOTALL)
    if not desc_match:
        desc_match = re.search(r'<div[^>]*class="formatted_description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    
    desc_text = ""
    if desc_match:
        desc_html = desc_match.group(1)
        desc_html = re.sub(r'<br\s*/?>|</p>|</div>', '\n', desc_html)
        desc_text = re.sub(r'<[^>]+>', '', desc_html)
        desc_text = unescape(desc_text.strip())
        desc_text = re.sub(r'\n\s*\n+', '\n\n', desc_text)
        
    # 4. Extract price from subpage schema markup
    price_match = re.search(r'itemprop="price"[^>]*>([^<]+)</span>', html)
    price = "FREE"
    if price_match:
        price_val = price_match.group(1).strip()
        clean_price = price_val.replace(" USD", "").strip()
        if clean_price.endswith(".00"):
            clean_price = clean_price[:-3]
        price = clean_price
    
    # 5. Info panel fields
    status_html = _parse_info_panel_row(html, "Status")
    status = re.sub(r'<[^>]+>', '', status_html).strip() if status_html else ""
    
    published_html = _parse_info_panel_row(html, "Published")
    published_date = _parse_date_from_abbr(published_html)
    
    updated_html = _parse_info_panel_row(html, "Updated")
    updated_date = _parse_date_from_abbr(updated_html)
    
    release_html = _parse_info_panel_row(html, "Release date")
    release_date = _parse_date_from_abbr(release_html)
    
    made_with_html = _parse_info_panel_row(html, "Made with")
    made_with = re.sub(r'<[^>]+>', '', made_with_html).strip() if made_with_html else ""
    
    tags_html = _parse_info_panel_row(html, "Tags")
    tags = []
    if tags_html:
        tags = [unescape(t.strip()) for t in re.findall(r'>([^<]+)</a>', tags_html) if t.strip()]
    
    # 6. Rating from schema markup
    rating_val_match = re.search(r'itemprop="ratingValue"[^>]*content="([^"]+)"', html)
    if not rating_val_match:
        rating_val_match = re.search(r'content="([^"]+)"[^>]*itemprop="ratingValue"', html)
    rating_value = float(rating_val_match.group(1)) if rating_val_match else 0
    
    rating_count_match = re.search(r'itemprop="ratingCount"[^>]*>(\d+)', html)
    if not rating_count_match:
        rating_count_match = re.search(r'content="(\d+)"[^>]*itemprop="ratingCount"', html)
    rating_count = int(rating_count_match.group(1)) if rating_count_match else 0
    
    # 7. Detect devlog link
    has_devlog = bool(re.search(r'class="[^"]*devlog_link[^"]*"', html))
    
    return {
        "banner": banner,
        "screenshots": screenshots,
        "longDescription": desc_text,
        "price": price,
        "status": status,
        "publishedDate": published_date,
        "updatedDate": updated_date,
        "releaseDate": release_date,
        "madeWith": made_with,
        "tags": tags,
        "ratingValue": rating_value,
        "ratingCount": rating_count,
        "hasDevlog": has_devlog
    }

def parse_devlog(game_url):
    """Scrape devlog posts from a game's /devlog page."""
    devlog_url = game_url.rstrip("/") + "/devlog"
    print(f"  Scraping devlog: {devlog_url} ...", flush=True)
    html = fetch_url(devlog_url)
    if not html:
        return []
    
    posts = []
    # Each devlog post is inside a <li> within the blog_post_list_widget
    post_blocks = re.findall(r'<li>(.*?)</li>', html, re.DOTALL)
    for block in post_blocks:
        # Title and URL
        title_match = re.search(r'<a\s+href="([^"]+)"\s+class="title"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not title_match:
            title_match = re.search(r'<a\s+class="title"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not title_match:
            continue
        
        post_url = title_match.group(1).strip()
        post_title = unescape(re.sub(r'<[^>]+>', '', title_match.group(2)).strip())
        
        # Extract devlog ID from URL (e.g., /devlog/1580691/added-controller-support)
        id_match = re.search(r'/devlog/(\d+)/', post_url)
        post_id = id_match.group(1) if id_match else ""
        
        # Date
        date_str = _parse_date_from_abbr(block)
        
        # Summary
        summary_match = re.search(r'<span\s+class="summary_text"[^>]*>(.*?)</span>', block, re.DOTALL)
        summary = ""
        if summary_match:
            summary = unescape(re.sub(r'<[^>]+>', '', summary_match.group(1)).strip())
        
        # Likes
        likes_match = re.search(r'class="post_likes"[^>]*>(\d+)', block)
        likes = int(likes_match.group(1)) if likes_match else 0
        
        # Image
        img_match = re.search(r'<img[^>]*class="post_image"[^>]*src="([^"]+)"', block)
        if not img_match:
            img_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="post_image"', block)
        post_image = img_match.group(1) if img_match else ""
        
        posts.append({
            "id": post_id,
            "title": post_title,
            "date": date_str,
            "summary": summary,
            "likes": likes,
            "url": post_url,
            "image": post_image
        })
    
    print(f"    Found {len(posts)} devlog post(s).", flush=True)
    return posts

def scrape_portfolio():
    # Load existing data.json to preserve manual edits and existing records
    existing_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            print(f"Loaded existing {DATA_FILE}. Merging manual edits...", flush=True)
        except Exception as e:
            print(f"Error reading existing {DATA_FILE}: {e}. Creating new dataset...", flush=True)
            
    existing_items = {}
    for category in ["games", "tools", "assets"]:
        for item in existing_data.get(category, []):
            if "id" in item:
                existing_items[item["id"]] = item
                
    print("Connecting to xtremezero.itch.io...", flush=True)
    main_html = fetch_url("https://xtremezero.itch.io/")
    if not main_html:
        print("Failed to fetch main itch.io profile page.")
        return
    
    # Identify collection blocks
    collection_blocks = re.split(r'<div[^>]*class="[^"]*collection_row[^"]*"', main_html)
    collections = []
    for block in collection_blocks[1:]:
        id_match = re.search(r'href="[^"]*/c/([^/"]+)/', block)
        title_match = re.search(r'<h2><a[^>]*>(.*?)</a></h2>', block, re.DOTALL)
        if id_match and title_match:
            coll_id = id_match.group(1)
            name = unescape(title_match.group(1).strip())
            collections.append((coll_id, name, block))
            
    print(f"Discovered {len(collections)} collections on profile.", flush=True)
    
    games = []
    tools = []
    assets = []
    
    for coll_id, name, inner_html in collections:
        print(f"\nProcessing Collection: '{name}' (ID: {coll_id})", flush=True)
        
        cells = re.split(r'(?=<div[^>]*data-game_id=")', inner_html)
        for cell in cells[1:]:
            game_id_match = re.search(r'data-game_id="([^"]+)"', cell)
            if not game_id_match:
                continue
            game_id = game_id_match.group(1)
            
            # URL
            link_match = re.search(r'href="([^"]+)"', cell)
            link = link_match.group(1) if link_match else ""
            
            # Title
            title_match = re.search(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>', cell, re.DOTALL)
            title = unescape(title_match.group(1).strip()) if title_match else "Unknown"
            
            # Thumbnail Image
            img_match = re.search(r'<img[^>]*data-lazy_src="([^"]+)"', cell)
            if not img_match:
                img_match = re.search(r'<img[^>]*src="([^"]+)"', cell)
            img = img_match.group(1) if img_match else ""
            
            # Short description
            desc_match = re.search(r'<div[^>]*class="game_text"[^>]*title="([^"]+)"', cell)
            if not desc_match:
                desc_match = re.search(r'<div[^>]*class="game_text"[^>]*>(.*?)</div>', cell, re.DOTALL)
            short_desc = unescape(desc_match.group(1).strip()) if desc_match else ""
            
            # Price
            price_match = re.search(r'<div[^>]*class="price_value"[^>]*>(.*?)</div>', cell)
            price = price_match.group(1).strip() if price_match else "FREE"
            
            # Genre
            genre_match = re.search(r'<div[^>]*class="game_genre"[^>]*>(.*?)</div>', cell)
            genre = genre_match.group(1).strip() if genre_match else "Assets" if "Assets" in name else "Tool" if "Tools" in name else "General"
            
            # Platforms
            platforms = []
            if 'class="web_flag"' in cell or 'Play in browser' in cell:
                platforms.append('Web')
            platform_icons = re.findall(r'class="icon icon-([^"\s]+)"', cell)
            for icon in platform_icons:
                if 'windows' in icon:
                    platforms.append('Windows')
                elif 'tux' in icon or 'linux' in icon:
                    platforms.append('Linux')
                elif 'apple' in icon or 'osx' in icon:
                    platforms.append('macOS')
                elif 'android' in icon:
                    platforms.append('Android')
            
            print(f"- Found Item: {title} ({game_id})", flush=True)
            
            # Polite latency
            time.sleep(0.3)
            
            # Scraping detailed sub-page data
            subpage = parse_subpage(link)
            
            # Construct product structure with all scraped fields
            item_data = {
                "id": game_id,
                "title": title,
                "genre": genre,
                "status": subpage["status"],
                "description": short_desc,
                "longDescription": subpage["longDescription"],
                "image": img,
                "bannerImage": subpage["banner"] if subpage["banner"] else img,
                "screenshots": subpage["screenshots"],
                "price": subpage["price"],
                "url": link,
                "platforms": platforms,
                "madeWith": subpage["madeWith"],
                "tags": subpage["tags"],
                "rating": subpage["ratingValue"] if subpage["ratingValue"] else 5.0,
                "ratingCount": subpage["ratingCount"],
                "publishedDate": subpage["publishedDate"],
                "updatedDate": subpage["updatedDate"],
                "releaseDate": subpage["releaseDate"] if subpage["releaseDate"] else "2024",
                "devlogs": []
            }
            
            # Scrape devlogs if available
            if subpage["hasDevlog"] and link:
                time.sleep(0.3)
                item_data["devlogs"] = parse_devlog(link)
            
            # Merge with existing item to preserve manual edits
            if game_id in existing_items:
                existing = existing_items[game_id]
                for key, val in existing.items():
                    # Preserve manually edited descriptions/genre if they differ
                    if key in ["description", "longDescription", "genre"] and val and item_data.get(key) != val:
                        item_data[key] = val
                    # Preserve descriptions/images if scraper failed but existing has them
                    elif key in ["description", "longDescription", "bannerImage", "screenshots"] and not item_data.get(key):
                        item_data[key] = val
                    # Preserve any custom keys not in the scraped data
                    elif key not in item_data:
                        item_data[key] = val
                
                existing_items[game_id]["_seen"] = True
            
            # Categorize items by collection name
            name_lower = name.lower()
            if "games" in name_lower or "collaborations" in name_lower:
                games.append(item_data)
            elif "tools" in name_lower or "plugin" in name_lower:
                tools.append(item_data)
            elif "assets" in name_lower or "showcase" in name_lower:
                assets.append(item_data)
            else:
                games.append(item_data) # fallback
                
    # Append any existing items that weren't scraped (e.g., manually added or unlisted)
    for game_id, item in existing_items.items():
        if not item.get("_seen"):
            # Put back in the correct category
            if any(x.get("id") == game_id for x in existing_data.get("games", [])):
                games.append(item)
            elif any(x.get("id") == game_id for x in existing_data.get("tools", [])):
                tools.append(item)
            elif any(x.get("id") == game_id for x in existing_data.get("assets", [])):
                assets.append(item)
            else:
                games.append(item) # fallback

    # Clean up _seen flag
    for item_list in [games, tools, assets]:
        for item in item_list:
            item.pop("_seen", None)

    # Preserve manual categories or assign defaults
    about = existing_data.get("about", DEFAULT_ABOUT)
    links = existing_data.get("links", DEFAULT_LINKS)
    
    # Build news from scraped devlogs + preserve manual news entries
    existing_news = existing_data.get("news", existing_data.get("newsItems", DEFAULT_NEWS))
    
    # Collect all devlog posts across all items as news candidates
    scraped_news = []
    all_items = games + tools + assets
    for item in all_items:
        for post in item.get("devlogs", []):
            scraped_news.append({
                "id": f"devlog-{post['id']}" if post['id'] else f"devlog-{item['id']}",
                "title": post["title"],
                "category": "DEVLOG",
                "date": post["date"],
                "image": post["image"] if post["image"] else item.get("image", ""),
                "summary": post["summary"],
                "likes": post["likes"],
                "url": post["url"],
                "gameTitle": item["title"]
            })
    
    # Merge: keep manual news entries (non-devlog), add scraped devlogs
    manual_news = [n for n in existing_news if not str(n.get("id", "")).startswith("devlog-")]
    scraped_ids = {n["id"] for n in scraped_news}
    # Also keep existing devlog news that weren't re-scraped (edge case)
    existing_devlog_news = [n for n in existing_news if str(n.get("id", "")).startswith("devlog-") and n["id"] not in scraped_ids]
    
    news = manual_news + scraped_news + existing_devlog_news
    # Sort by date descending (newest first)
    news.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    print(f"\nTotal news items: {len(news)} ({len(manual_news)} manual + {len(scraped_news)} from devlogs)", flush=True)
    
    # Build complete catalog payload
    output_payload = {
        "about": about,
        "links": links,
        "news": news,
        "games": games,
        "tools": tools,
        "assets": assets
    }
    
    # Save back to data.json
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully wrote updated data to {DATA_FILE}!", flush=True)
    except Exception as e:
        print(f"\nFailed to save {DATA_FILE}: {e}", flush=True)

if __name__ == "__main__":
    scrape_portfolio()
