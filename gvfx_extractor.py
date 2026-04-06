import urllib.request
import re
import json
import time

def to_pine_color(rgba_str):
    if not rgba_str:
        return "color.new(color.blue, 0)"
    if rgba_str.startswith('#'):
        return f"color.from_gradient(0, 0, 1, color.new(color.gray, 50), color.new(color.gray, 50))"
        
    rgba_str = rgba_str.strip()
    if rgba_str.startswith('rgba'):
        match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\)', rgba_str)
        if match:
            r, g, b, a = match.groups()
            pine_transp = 100 - int(float(a) * 100)
            return f"color.rgb({r}, {g}, {b}, {pine_transp})"
    elif rgba_str.startswith('rgb'):
        match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgba_str)
        if match:
            r, g, b = match.groups()
            return f"color.rgb({r}, {g}, {b}, 0)"
    elif rgba_str.startswith('#'):
        h = rgba_str.lstrip('#')
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"color.rgb({r}, {g}, {b}, 0)"
            
    return "color.new(color.blue, 0)"

print("Connecting to TradingView RSS Feed for Goldviewfx...")
rss_url = "https://www.tradingview.com/feed/?username=Goldviewfx"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
req = urllib.request.Request(rss_url, headers=headers)
try:
    xml = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
except Exception as e:
    print(f"Failed to fetch user feed: {e}")
    exit(1)

# Find the latest GOLD 1H charting article
items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL | re.IGNORECASE)
latest_link = None
report_title = "Unknown"
for item in items:
    title_match = re.search(r'<title>(.*?)</title>', item)
    if title_match:
        title = title_match.group(1).upper()
        if 'GOLD' in title and '1H' in title:
            link_match = re.search(r'<link>(https://www.tradingview.com/chart/[^<]+)</link>', item)
            if link_match:
                latest_link = link_match.group(1)
                report_title = title_match.group(1)
                break

if not latest_link:
    # If no specific 'GOLD 1H' title matched, try to find one with just GOLD, or fallback to first
    print("Could not find article strictly matching 'GOLD' and '1H'. Attempting fallback...")
    for item in items:
        title_match = re.search(r'<title>(.*?)</title>', item)
        if title_match and 'GOLD' in title_match.group(1).upper():
            link_match = re.search(r'<link>(https://www.tradingview.com/chart/[^<]+)</link>', item)
            if link_match:
                latest_link = link_match.group(1)
                report_title = title_match.group(1)
                break
                
    if not latest_link:
        print("No chart URL found related to gold!")
        exit(1)

print(f"Found Target Chart: {report_title} -> {latest_link}")

# Download the Chart payload
chart_req = urllib.request.Request(latest_link, headers=headers)
try:
    html = urllib.request.urlopen(chart_req, timeout=15).read().decode('utf-8')
except Exception as e:
    print(f"Failed to download chart HTML: {e}")
    exit(1)

# Extract any shape LineTool structures 
print("Extracting drawing entities from nested TradingView environment...")
pattern = r'\{\\?"type\\?":\\?"LineTool(HorzLine|HorzRay|Ray|TrendLine|PriceLabel|Text)\\?"'
shapes = []
idx = 0
while True:
    match = re.search(pattern, html[idx:])
    if not match:
        break
        
    start_idx = idx + match.start()
    brace_count = 0
    end_idx = start_idx
    in_string = False
    escape = False
    
    for i in range(start_idx, len(html)):
        char = html[i]
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
                    
    if brace_count == 0:
        json_str = html[start_idx:end_idx]
        try:
            clean_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
            shapes.append(json.loads(clean_str))
        except:
            pass
    idx = start_idx + 10

print(f"Discovered {len(shapes)} raw line objects.")

target_lines = []
for obj in shapes:
    text = obj.get('state', {}).get('text', '').lower()
    
    # User's conditions: caption contains "goldturn", "gold price", or "gold turn"
    if 'gold price' in text or 'gold turn' in text or 'goldturn' in text:
        points = obj.get('points', [])
        prices = [float(p['price']) for p in points if p.get('price') is not None]
        
        # Check alternative state formatting if points are empty
        if not prices:
            price = obj.get('state', {}).get('price')
            if price is not None:
                prices.append(float(price))
                
        if prices:
            target_lines.append({
                'type': obj.get('type', ''),
                'price': prices[0], # horizontal lines mostly just need one price axis
                'text': obj.get('state', {}).get('text', ''),
                'color': obj.get('state', {}).get('color', obj.get('state', {}).get('linecolor', ''))
            })

# Remove duplicates
unique_lines = []
seen_prices = set()
for t in target_lines:
    if t['price'] not in seen_prices:
        seen_prices.add(t['price'])
        unique_lines.append(t)

print(f"Filtered to {len(unique_lines)} critical Gold Level lines!")

pine_filename = "gvfx_gold_levels.pine"
pine_code = [
    "//@version=5",
    "indicator(\"GVFX Gold Levels\", overlay=true)",
    "",
    "if barstate.islast"
]

if not unique_lines:
    pine_code.append("    // No lines found matching 'gold price' or 'gold turn'")
else:
    for line in unique_lines:
        price = line['price']
        color = to_pine_color(line['color'])
        true_text = line['text'].replace('\n', ' ').strip()
        
        # We draw a line extending both sides, mimicking a horizontal line
        pine_code.append(f"    line.new(x1=bar_index[1], y1={price}, x2=bar_index, y2={price}, extend=extend.both, color={color}, width=2)")
        # We place a label anchored on the line labeling it gvfx
        pine_code.append(f"    label.new(x=bar_index, y={price}, text='gvfx: {true_text}', textcolor={color}, color=color.new(color.white, 100), style=label.style_label_left, size=size.normal)")

with open(pine_filename, 'w', encoding='utf-8') as f:
    f.write('\n'.join(pine_code))
    
print(f"Pine Script code completely generated: {pine_filename}")
