import json
import re

def extract_all_shapes():
    with open('tv.html', 'r', encoding='utf-8') as f:
        html = f.read()

    match = re.search(r'window\.initData\s*=\s*(\{.*?\});\s*(?:window\.|</script>|$)', html, re.DOTALL)
    if not match:
        print("Could not find window.initData")
        return

    data = json.loads(match.group(1))
    
    shapes = []
    
    def search_and_parse(obj):
        if isinstance(obj, dict):
            typ = obj.get('type')
            if isinstance(typ, str) and typ.startswith('LineTool'):
                shapes.append(obj)
            for k, v in obj.items():
                search_and_parse(v)
        elif isinstance(obj, list):
            for item in obj:
                search_and_parse(item)
        elif isinstance(obj, str):
            if 'LineTool' in obj:
                # Need to handle potential nested stringified JS.
                # Try to parse string as JSON
                try:
                    parsed = json.loads(obj)
                    search_and_parse(parsed)
                except:
                    pass

    search_and_parse(data)
    
    print(f"Found {len(shapes)} shapes!")
    
    # Process properties
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
        
        # We classify shapes to return cleanly to user!
        state = obj.get('state', {})
        if 'color' in state:
            shape['color'] = state['color']
        if 'backgroundColor' in state:
            shape['backgroundColor'] = state['backgroundColor']
            
        final_output.append(shape)
        
    with open('final_shapes.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)

extract_all_shapes()
