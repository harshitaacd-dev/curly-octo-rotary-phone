# Google Trends data (to be pulled locally)

Google blocks Trends requests from the cloud environment this repository was built in (HTTP 429
even for the Trends home page), so the pull has to run on your own computer:

```
pip install pytrends pandas
python scripts/trends_pull.py --out data/external/google_trends --sample-id 1
# ideally again on two other days, to average out Google's sampling noise:
python scripts/trends_pull.py --out data/external/google_trends --sample-id 2
python scripts/trends_pull.py --out data/external/google_trends --sample-id 3
# optional, ~180 extra requests: per-state monthly series for the core terms
python scripts/trends_pull.py --out data/external/google_trends --sample-id 1 --state-monthly
```

- **Size:** about 45 requests per sample, ~20 seconds apart, so roughly 15–20 minutes.
- **Resuming:** responses are cached in `raw/`. If Google returns 429, stop, wait an hour and
  re-run the same command; it continues where it stopped.
- **Search terms:** edit `GROUPS` in `scripts/trends_pull.py` to add Hindi or regional terms and
  app names. The Hindi terms there are a starting point and need checking.

Then estimate Part B with Trends exposure:

```
python scripts/partB_estimate.py --exposure trends --trends data/external/google_trends --out analysis/partB_trends
```

Commit the CSVs and `raw/` so the analysis is reproducible.
