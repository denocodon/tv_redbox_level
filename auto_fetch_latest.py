import urllib.request
import re
import sys
from datetime import datetime
from tv_extractor import process_chart

def get_latest_chart_info(profile_url_or_username):
    if "tradingview.com/u/" in profile_url_or_username:
        username = profile_url_or_username.rstrip('/').split('/')[-1]
    else:
        username = profile_url_or_username

    print(f"Resolving latest chart for user: {username}...")
    rss_url = f"https://www.tradingview.com/feed/?username={username}"
    
    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        xml = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch user feed: {e}")
        return None, None

    item_match = re.search(r'<item>(.*?)</item>', xml, re.DOTALL | re.IGNORECASE)
    if not item_match:
        print("No items found.")
        return None, None
        
    item_xml = item_match.group(1)
    
    link_match = re.search(r'<link>(https://www.tradingview.com/chart/[^<]+)</link>', item_xml)
    date_match = re.search(r'<pubDate>([^<]+)</pubDate>', item_xml)
    
    if not link_match:
        print("No chart URL found in the latest item!")
        return None, None
        
    latest_url = link_match.group(1)
    
    report_date = "Unknown_Date"
    if date_match:
        raw_date = date_match.group(1).strip()
        try:
            dt = datetime.strptime(raw_date[:25].strip(), "%a, %d %b %Y %H:%M:%S")
            report_date = dt.strftime("%Y-%m-%d")
        except:
            report_date = re.sub(r'[^a-zA-Z0-9]', '_', raw_date[:16])
            
    print(f"Found latest chart: {latest_url} from {report_date}")
    return latest_url, report_date

if __name__ == "__main__":
    profile_input = "https://www.tradingview.com/u/KnightsofGold/"
    days = 30
    
    if len(sys.argv) >= 2:
        profile_input = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            days = float(sys.argv[2])
        except ValueError:
            print("Error: days must be numeric.")
            sys.exit(1)
            
    latest_url, report_date = get_latest_chart_info(profile_input)
    if latest_url:
        print(f"Processing extraction for {days} days limit...")
        process_chart(latest_url, days, report_date)
