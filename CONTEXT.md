# Antigravity Context: TradingView Shape Extractor Toolkit

Hello Antigravity. If you are reading this file, you have been requested to load the context for this repository on a new machine.

## Project Summary
This project Automates the extraction of TradingView chart data (specifically dynamically drawn shapes like Rectangles and Circles) from public charts and converts them into runnable TradingView Pine Scripts for overlays. It was specifically built to extract from the "KnightsofGold" user profile.

## Key Files & Technologies
- **Python Scripts**: The core scraper and Pine Script generation logic. 
  - `auto_fetch_latest.py`: Uses RSS feeds to bypass heavy JS scraping to find the absolute newest TradingView chart from a profile.
  - `tv_extractor.py`: The actual extraction logic that parses specific TradingView shapes and outputs a pine script.
  - `generate_pine.py`: Helper logic taking extracted `json` data to construct `.pine` code.
- **Pine Script Output**: Yields a `.pine` file that perfectly scales coordinates to absolute time properties.

## Recent Conventions & Notes
- We recently updated the box drawing logic (`box.new` in Pine Script generation). All generated rectangles must now include the `extend=extend.right` attribute. 
  - *Example output*: `box.new(..., xloc=xloc.bar_time, extend=extend.right)`
- Data outputs are largely dependent on fetching and extracting from chronological feeds rather than visual rendering, limiting issues with CAPTCHAs.

## Instructions
1. Familiarize yourself with `tv_extractor.py`, `generate_pine.py`, and `auto_fetch_latest.py`.
2. Do not override the Pine Script outputs manually without ensuring the `extend.right` box logic remains intact.
3. This is a PowerShell / Windows environment generally.

You are now fully caught up on the most important context for this codebase!
