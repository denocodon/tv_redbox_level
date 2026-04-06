import json
import re
import datetime

with open('kog_shapes_extracted_10days.json', 'r', encoding='utf-8') as f:
    shapes = json.load(f)

# Helper to convert rgba string to pinescript color
def to_pine_color(rgba_str):
    if not rgba_str:
        return "color.new(color.gray, 50)"
    if rgba_str.startswith('#'):
        return f"color.from_gradient(0, 0, 1, color.new(color.gray, 50), color.new(color.gray, 50))" # fallback for simple hex, but let's parse hex
        
    rgba_str = rgba_str.strip()
    if rgba_str.startswith('rgba'):
        match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\)', rgba_str)
        if match:
            r, g, b, a = match.groups()
            # Pine transp is 0 (opaque) to 100 (invisible)
            pine_transp = 100 - int(float(a) * 100)
            return f"color.rgb({r}, {g}, {b}, {pine_transp})"
    elif rgba_str.startswith('rgb'):
        match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgba_str)
        if match:
            r, g, b = match.groups()
            return f"color.rgb({r}, {g}, {b}, 0)"
    elif rgba_str.startswith('#'):
        # Just hex
        h = rgba_str.lstrip('#')
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"color.rgb({r}, {g}, {b}, 0)"
            
    return "color.new(color.gray, 50)"

pine_code = []
pine_code.append("//@version=5")
pine_code.append("indicator(\"Extracted KOG Shapes\", overlay=true)")
pine_code.append("")
pine_code.append("if barstate.islast")

for i, s in enumerate(shapes):
    typ = s['type']
    start_ms = int(s['start_time'] * 1000)
    end_ms = int(s['end_time'] * 1000)
    t_price = s['top_price']
    b_price = s['bottom_price']
    
    border_color = to_pine_color(s.get('color', ''))
    bg_color = to_pine_color(s.get('backgroundColor', ''))
    
    text = s.get('text', '').replace('\n', ' ').strip()
    
    if typ == "Rectangle":
        # Draw a box
        pine_code.append(f"    box.new(left={start_ms}, top={t_price}, right={end_ms}, bottom={b_price}, text='{text}', border_color={border_color}, bgcolor={bg_color}, xloc=xloc.bar_time, extend=extend.right)")
    elif typ == "Circle":
        # Pine script has no true circle object. We usually use a box with round corners, or a label. 
        # A box works well to visually outline the range. But let's use a label if the user wants exactly a circle.
        # But a label only has one y/x coordinate.
        # Let's draw a box but maybe with a custom style. Or just a label mapping.
        # "To approximate a circle over a time/price range, we will draw a label at the center."
        center_ms = int((start_ms + end_ms) / 2)
        center_price = (t_price + b_price) / 2
        dt_str = datetime.datetime.utcfromtimestamp(center_ms / 1000).strftime('%Y-%m-%d %H:%M UTC')
        pine_code.append(f"    // Circle approximated as a label at {dt_str}")
        pine_code.append(f"    label.new(x={center_ms}, y={center_price}, style=label.style_circle, color={bg_color}, size=size.normal, xloc=xloc.bar_time, tooltip='{dt_str}')")

with open('draw_shapes.pine', 'w', encoding='utf-8') as f:
    f.write('\n'.join(pine_code))

print("Pine script written to draw_shapes.pine")
