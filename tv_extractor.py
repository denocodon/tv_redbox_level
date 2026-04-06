import urllib.request
import re
import json
import time
import sys
import datetime
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def to_pine_color(rgba_str):
    if not rgba_str:
        return "color.new(color.gray, 50)"
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
            
    return "color.new(color.gray, 50)"

def process_chart(url, days, report_date=None):
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch URL: {e}")
        return

    pattern = r'\{\\?"type\\?":\\?"LineTool(Rectangle|Ellipse|Circle)\\?"'
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

    print(f"Found {len(shapes)} raw shapes...")
    
    current_time = time.time()
    target_days_sec = days * 24 * 60 * 60
    min_time = current_time - target_days_sec
    max_time = current_time + target_days_sec
    
    filtered_shapes = []
    for obj in shapes:
        points = obj.get('points', [])
        times = []
        prices = []
        for p in points:
            t = p.get('time_t') or p.get('time')
            if t is not None:
                times.append(float(t))
            if 'price' in p and p['price'] is not None:
                prices.append(float(p['price']))
                
        in_window = False
        if len(times) >= 2:
            start_t = min(times)
            end_t = max(times)
            if start_t <= max_time and end_t >= min_time:
                in_window = True
        elif len(times) == 1:
            if min_time <= times[0] <= max_time:
                in_window = True

        if in_window:
            typ = obj.get('type', '').replace('LineTool', '').replace('Ellipse', 'Circle')
            if not prices: continue
            shape = {
                'type': typ,
                'top_price': max(prices),
                'bottom_price': min(prices),
                'start_time': min(times),
                'end_time': max(times),
                'text': obj.get('state', {}).get('text', ''),
                'color': obj.get('state', {}).get('color', ''),
                'backgroundColor': obj.get('state', {}).get('backgroundColor', '')
            }
            filtered_shapes.append(shape)
            
    unique_shapes = []
    seen = set()
    for s in filtered_shapes:
        key = (s['type'], s.get('top_price'), s.get('bottom_price'), s.get('color'), s.get('backgroundColor'), s.get('start_time'), s.get('end_time'))
        if key not in seen:
            seen.add(key)
            unique_shapes.append(s)
            
    print(f"Filtered to {len(unique_shapes)} shapes within {days} days of today.")

    pine_title = f"KOG Report {report_date}" if report_date else "Extracted Pine Shapes"
    pine_filename = f"KOG_Report_{report_date}.pine" if report_date else "output.pine"

    pine_code = [
        "//@version=5",
        f"indicator(\"{pine_title}\", overlay=true)",
        "",
        "if barstate.islast"
    ]
    
    for s in unique_shapes:
        start_ms = int(s['start_time'] * 1000)
        end_ms = int(s['end_time'] * 1000)
        t_price = s['top_price']
        b_price = s['bottom_price']
        border_color = to_pine_color(s['color'])
        bg_color = to_pine_color(s['backgroundColor'])
        text = s['text'].replace('\n', ' ').strip()
        
        if s['type'] == "Rectangle":
            pine_code.append(f"    box.new(left={start_ms}, top={t_price}, right={end_ms}, bottom={b_price}, text='{text}', border_color={border_color}, bgcolor={bg_color}, xloc=xloc.bar_time, extend=extend.right)")
        elif s['type'] == "Circle":
            center_ms = int((start_ms + end_ms) / 2)
            c_price = (t_price + b_price) / 2
            dt_str = datetime.datetime.utcfromtimestamp(center_ms / 1000).strftime('%Y-%m-%d %H:%M UTC')
            pine_code.append(f"    // Circle approximated as a label at {dt_str}")
            pine_code.append(f"    label.new(x={center_ms}, y={c_price}, style=label.style_circle, color={bg_color}, size=size.normal, xloc=xloc.bar_time, tooltip='{dt_str}')")

    if len(unique_shapes) == 0:
        pine_code.append(f"    // No shapes found within {days} days")

    with open(pine_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(pine_code))
        
    print(f"Done! Pine script generated at: {pine_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tv_extractor.py <tradingview_url> [days]")
        print("Example: python tv_extractor.py https://... 30")
    else:
        url = sys.argv[1]
        days = 10
        if len(sys.argv) >= 3:
            try:
                days = float(sys.argv[2])
            except ValueError:
                print("Error: days must be a number.")
                sys.exit(1)
                
        process_chart(url, days)
