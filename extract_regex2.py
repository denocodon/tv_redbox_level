import json
import re

with open('tv.html', 'r', encoding='utf-8') as f:
    html = f.read()

# We look for the "type" property with or without escapes
# We can just unescape the entire html when searching? No, that would break structure.
# Let's just find the pattern
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
        # In a stringified json, the string has \". We need to replace \" with " to parse it, 
        # or it might already be valid if we decode the outer string.
        # Let's try to parse as-is. If it fails, maybe we unescape it first.
        try:
            # If it's something like {\"type\":\"...\"}, it's technically invalid JSON. 
            # We fix it by doing a simple unescape:
            clean_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
            shape_obj = json.loads(clean_str)
            shapes.append(shape_obj)
        except Exception as e:
            print("Failed to parse:", json_str[:100], "Error:", e)
            
    idx = start_idx + 10 # Move past the starting brace

print(f"Matcher found {len(shapes)} shapes!")

final_output = []
for obj in shapes:
    typ = obj.get('type')
    shape = {'type': typ}
    points = obj.get('points', [])
    prices = [float(p['price']) for p in points if 'price' in p and p['price'] is not None]
    if prices:
        shape['top_price'] = max(prices)
        shape['bottom_price'] = min(prices)
    else:
        shape['top_price'] = None
        shape['bottom_price'] = None

    text = obj.get('state', {}).get('text', '')
    if text:
        shape['text'] = text
    
    state = obj.get('state', {})
    if 'color' in state:
        shape['color'] = state['color']
    if 'backgroundColor' in state:
        shape['backgroundColor'] = state['backgroundColor']
        
    final_output.append(shape)

with open('bracket_parsed_shapes.json', 'w', encoding='utf-8') as f:
    json.dump(final_output, f, indent=2)

print("Saved to bracket_parsed_shapes.json")
