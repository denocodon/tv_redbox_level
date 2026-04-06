import json

with open('extracted_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

extracted_shapes = []

def extract_shapes(obj):
    if isinstance(obj, dict):
        typ = obj.get('type')
        if typ and typ.startswith('LineTool'):
            # It's a shape! Let's get its properties
            shape = {'type': typ}
            points = obj.get('points', [])
            prices = [p['price'] for p in points if 'price' in p]
            if prices:
                shape['top_price'] = max(prices)
                shape['bottom_price'] = min(prices)
            else:
                shape['top_price'] = None
                shape['bottom_price'] = None

            text = obj.get('state', {}).get('text', '')
            if text:
                shape['text'] = text
            
            # color or other ident properties
            state = obj.get('state', {})
            if 'color' in state:
                shape['color'] = state['color']
            if 'backgroundColor' in state:
                shape['backgroundColor'] = state['backgroundColor']

            extracted_shapes.append(shape)
            
        for k, v in obj.items():
            extract_shapes(v)
    elif isinstance(obj, list):
        for item in obj:
            extract_shapes(item)

extract_shapes(data)

# Save the final results to prices.json
with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(extracted_shapes, f, indent=2)

print(f"Extracted {len(extracted_shapes)} shapes to prices.json")
# Print uniquely found shape types
types = set(s['type'] for s in extracted_shapes)
print("Shape types found:", types)
