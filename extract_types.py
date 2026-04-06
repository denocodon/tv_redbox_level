import json
import re

with open('tv.html', 'r', encoding='utf-8') as f:
    text = f.read()

types = set(re.findall(r'"type":"(LineTool.*?)"', text))
print('LineTool types found in tv.html:', types)

# Let's extract ALL objects with type LineTool... into a structured list
shapes = []
# The payload is likely in window.initData or similar script tags.
# A simpler way is to find all JSON-like objects that contain "type":"LineTool..."
# Since regex parsing of nested JSON is hard, we can try to extract the main JSON block.
# Let's search for "LineToolRectangle" and find its enclosing context.

# Let's find window.initData
match = re.search(r'window\.initData\s*=\s*(\{.*?\});\s*(?:window\.|</script>|$)', text, re.DOTALL)
if match:
    # It might be stringified inside window.initData
    data_str = match.group(1)
    
    # Many times, the actual chart data is embedded as a string!
    # For example: window.initData.publishedCharts[...].content or something
    # Let's extract ALL string literals that might contain JSON with LineToolRectangle
    
    strings = set(re.findall(r'"(\{.*?(?:LineToolRectangle).*?\})"', data_str))
    print(f"Found {len(strings)} stringified JSON candidates.")
    
    # We can also just search the data_str for all JSON objects.
    # But since Python's json can decode the whole window.initData, let's do that.
    try:
        data = json.loads(data_str)
        # We need a recursive search to handle nested strings that contain JSON
        def search_dict(d, results):
            if isinstance(d, dict):
                for k, v in d.items():
                    search_dict(v, results)
            elif isinstance(d, list):
                for item in d:
                    search_dict(item, results)
            elif isinstance(d, str):
                if 'LineToolRectangle' in d:
                    try:
                        parsed = json.loads(d)
                        results.append(parsed)
                        # We might need to search the parsed dict too
                        search_dict(parsed, results)
                    except:
                        pass
        results = []
        search_dict(data, results)
        print(f"Extracted {len(results)} JSON structures containing LineTool")
        
        # Now save the results
        with open('extracted_data.json', 'w', encoding='utf-8') as out:
            json.dump(results, out, indent=2)
            
    except Exception as e:
        print("Error parsing initData", e)
