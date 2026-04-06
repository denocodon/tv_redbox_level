import json
import re

with open('tv.html', 'r', encoding='utf-8') as f:
    html = f.read()

# The data in matches_html.txt looks like it's part of a JSON array of shapes.
# Let's try to extract ALL occurrences of JSON objects describing LineToolRectangle/LineToolCircle/LineToolEllipse.
# A regex that matches {"type":"LineToolRectangle", ... "points":[...] ... }

# Since JSON matching with regex can be tricky with nesting, we can just extract everything between
# {"type":"LineToolRectangle" and the next {"type":"LineTool... or the end of the array.
# Better way: find all "type":"LineToolRectangle" and then use a brace-matching algorithm to extract the object.

shapes = []

idx = 0
while True:
    match = re.search(r'\{"type":"LineTool(?:Rectangle|Ellipse|Circle)"', html[idx:])
    if not match:
        break
    
    start_idx = idx + match.start()
    
    # We found the start of a dictionary '{'
    # Use a stack to find the corresponding '}'
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
            shape_obj = json.loads(json_str)
            shapes.append(shape_obj)
        except Exception as e:
            print("Failed to parse:", json_str[:100], "Error:", e)
            
    idx = start_idx + len('{"type":"LineTool')

print(f"Brace matcher found {len(shapes)} shapes!")

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
