import json

with open('bracket_parsed_shapes.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

# The user asks to "extract object properties a chart in browser, these object in 2 shapes group: rectangle and circle. You need to extract price from above/below to json"
# It's better to just ensure the output is small and deduped to be given as max quality.
# Let's deduplicate based on all properties.
unique_shapes = []
seen = set()

for s in shapes:
    # use a tuple of frozen items as key
    if s['top_price'] == s['bottom_price'] == None:
        continue
    key = (s['type'], s.get('top_price'), s.get('bottom_price'), s.get('color'), s.get('backgroundColor'))
    if key not in seen:
        seen.add(key)
        # Rename LineToolEllipse to Circle and LineToolRectangle to Rectangle for the user
        s['type'] = s['type'].replace('LineToolEllipse', 'Circle').replace('LineToolRectangle', 'Rectangle')
        unique_shapes.append(s)

with open('kog_shapes_extracted.json', 'w', encoding='utf-8') as f:
    json.dump(unique_shapes, f, indent=2)

print(f"Deduped shapes: {len(unique_shapes)}")
