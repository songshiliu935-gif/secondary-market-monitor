# Market Book

An English-language daily secondary-market monitor covering global indices, commodities, FX, Treasury yields, volatility and sector transmission.

## Run

1. Install Python 3.10+.
2. From this folder run `python update_market_book.py` after the US close.
3. Start a local web server and open `index.html` (or run `open_market_book.ps1` on Windows).

To register the daily Windows task, run `powershell -ExecutionPolicy Bypass -File .\setup_daily_task.ps1`. It runs at 08:30 Australia/Sydney time and starts when the computer becomes available.

The Windows task also writes a complete English Markdown brief to the Desktop under `Market Briefs`, with both a dated file such as `Market_Brief_2026-10-07.md` and `Latest_Market_Brief.md`. GitHub Actions updates the web snapshot; the local Windows task is what creates the Desktop copy.

The updater uses public Yahoo Finance and FRED data, calculates close-to-close returns, and compares the latest return with the previous 60 trading days. The dashboard presents this as an unusual-move score. Signals are: Watchlist (score >= 1), Significant (score >= 2), and Major (score >= 3).

The updater checks public official RSS feeds from the Federal Reserve and EIA, plus monitored Google News RSS searches, for the last 36 hours. Keyword matches are shown as `Likely` with source links; unmatched explanations remain `Hypothesis` and include a clickable latest-news search link. Headlines, links and timestamps are stored, not article bodies.
