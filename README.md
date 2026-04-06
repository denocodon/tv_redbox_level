# TradingView Shape Extractor Toolkit

An automated system designed to extract dynamically drawn shapes (like Rectangles and Circles) from public TradingView charts and convert them instantly into a runnable TradingView Pine Script for overlays. 

This environment has two modular parts: a master script for generic profiling (`tv_extractor.py`), and a highly targeted intelligent cronjob utility tailored inherently for KnightsofGold (`auto_fetch_latest.py`).

---

## What Does it Do?
- **Deep Extraction Strategy**: Bypasses heavy HTML/JS string protections, penetrating deep nesting elements inside TradingView architectures seamlessly.
- **Dynamic Time Limit Limit**: Automatically skips old shapes and limits its analysis strictly to active time windows (defaulted to 10 days) of execution time.
- **Pine Script Output Generation**: Yields a ready-to-run `.pine` document accurately reconstructed with perfectly scaled absolute coordinates, custom aesthetic shades, and automatic Pine formatting labels.

---

## Core Pipeline Tools

### 1. The Automated Fetch Hub (`auto_fetch_latest.py`) 
The backbone script to run everything dynamically on auto-pilot. 

**How it works seamlessly and knows what's latest:**
Instead of scraping graphical profiles which often trigger CAPTCHAs, this script connects to TradingView’s underlying RSS (Really Simple Syndication) architecture (`https://www.tradingview.com/feed/?username=[Name]`). 
By web standard, RSS feeds sequentially publish output in a structurally descending temporal pattern mapping. Because of this chronological rule, grabbing the extremely first index inside the script (`links[0]`) flawlessly secures exclusively the absolute newest broadcasted chart payload by that specific author, entirely dodging timestamps limits instantly.

**Smart Defaults:**
By natively running the script without any parameters, the internal logic defaults mapping directly to **`https://www.tradingview.com/u/KnightsofGold/`**, parses their feed chronologically, extracts the pubDate, and spits out a dynamic output file matching the publication date like: `KOG_Report_2026-04-05.pine`.

#### How to Excecute:
Run precisely inside your Terminal or PowerShell to execute a 10-day limit retrieval window natively:
```bash
python auto_fetch_latest.py
```
Should you want to map another profile link, or perhaps search up to a **30 Day Window Limits**, you just execute custom arguments:
```bash
python auto_fetch_latest.py "https://www.tradingview.com/u/SomeOtherUserName/" 30
```

### 2. Manual Chart Extractor (`tv_extractor.py`)
If you require retrieving a specific chart arbitrarily that is no longer the "latest", use this standalone script instead.

```bash
# General Command Example (Defaults to 10 days limits):
python tv_extractor.py "https://www.tradingview.com/chart/XAUUSD/id0a1NJQ-THE-KOG-REPORT-Update/"
```

---

## Applying The Pine Output
Following execution, inside the folder a `.pine` file will be generated.
1. Jump to TradingView on your web browser. 
2. At the bottom layout, pop open your **Pine Editor** tab.
3. Completely replace all active text in the editing console with the `output.pine` text exactly via paste. 
4. Select **Add to chart**. The elements will materialize perfectly over your UI mapping the extracted boundaries!

---

## Full Automation Setup (Cronjob)
You can configure a ghost-schedule ensuring that the script operates routinely without supervision—specifically set up to extract shapes at **5 AM, Monday Weekly**.

### Windows Users (Task Scheduler - Recommended)
The best procedure for raw Windows Environments ignores Chron arrays and utilizes native Windows capabilities:
1. Hit `Win + R`, invoke `taskschd.msc`, and press ENTER.
2. In the right panel, generate a **Create Basic Task...** titled: `KOG Auto Extractor`.
3. Set Trigger condition to **Weekly**, specifying **Monday**, adjusting launch to **05:00:00 AM**.
4. In the Action field, define **Start a program**.
5. Pass execution argument `python` natively into Program/Script blocks.
6. Target the "Add Arguments": `auto_fetch_latest.py`.
7. Define "Start In" field to exact script location: `C:\Users\Cuser\Documents\kog_extract\`
8. Hit Finish. Your setup will now reliably run securely behind the scenes.

### Traditional Command Linux/WSL Users (Crontab)
Open your operational bash instances, input command shell `crontab -e`, and structure this automated sequence exactly:
```bash
0 5 * * 1 cd /mnt/c/Users/Cuser/Documents/kog_extract && python auto_fetch_latest.py
```
*(Legend translation: Exact Minute 0, Base Hour 5, Any Day Limits `*`, Execution targeted to Day `1` Mapping Monday).*
