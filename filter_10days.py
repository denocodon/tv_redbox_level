import json
import re
import time

with open('tv.html', 'r', encoding='utf-8') as f:
    html = f.read()

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
            shape_obj = json.loads(clean_str)
            shapes.append(shape_obj)
        except Exception as e:
            pass
            
    idx = start_idx + 10

# Now shapes have all their raw properties
current_time = time.time()
# The dates might be in seconds or ms. Tradingview's `time_t` is usually in seconds.
# Let's filter to shapes which have AT LEAST ONE point within [current_time - 10 days, current_time + 10 days]?
# Or the user said "in 10 days from now". So maybe future limit up to 10 days from now?
# Just to be safe, I'll allow shapes where ANY of their timestamps is within [current_time - 10 days, current_time + 10 days].

ten_days_sec = 10 * 24 * 60 * 60
min_time = current_time - ten_days_sec
max_time = current_time + ten_days_sec

filtered_shapes = []
for obj in shapes:
    points = obj.get('points', [])
    times = []
    prices = []
    
    for p in points:
        # time_t or time inside p
        t = p.get('time_t') or p.get('time')
        if t is not None:
            times.append(float(t))
        
        if 'price' in p and p['price'] is not None:
            prices.append(float(p['price']))
            
    # Check if this shape touches the window
    # If the shape spans across the window, or is inside the window
    in_window = False
    if len(times) >= 2:
        start_t = min(times)
        end_t = max(times)
        # overlaps window
        if start_t <= max_time and end_t >= min_time:
            in_window = True
    elif len(times) == 1:
        if min_time <= times[0] <= max_time:
            in_window = True
    else:
        # no times, skip or keep? Let's skip
        pass

    if in_window:
        typ = obj.get('type', '').replace('LineTool', '')
        shape = {'type': typ}
        
        if prices:
            shape['top_price'] = max(prices)
            shape['bottom_price'] = min(prices)
        else:
            shape['top_price'] = None
            shape['bottom_price'] = None
            
        # Also let's output the timestamps so the user can verify
        shape['start_time'] = min(times)
        shape['end_time'] = max(times)

        text = obj.get('state', {}).get('text', '')
        if text:
            shape['text'] = text
        
        state = obj.get('state', {})
        if 'color' in state:
            shape['color'] = state['color']
        if 'backgroundColor' in state:
            shape['backgroundColor'] = state['backgroundColor']
            
        filtered_shapes.append(shape)

# Deduplicate
unique_shapes = []
seen = set()
for s in filtered_shapes:
    key = (s['type'], s.get('top_price'), s.get('bottom_price'), s.get('color'), s.get('backgroundColor'), s.get('start_time'), s.get('end_time'))
    if key not in seen:
        seen.add(key)
        unique_shapes.append(s)

# Also let's print some info to verify we got the timestamps right
print(f"Total shapes: {len(shapes)}")
print(f"Shapes overlapping last/next 10 days: {len(unique_shapes)}")

# Write to file
with open('kog_shapes_extracted_10days.json', 'w', encoding='utf-8') as f:
    json.dump(unique_shapes, f, indent=2)

