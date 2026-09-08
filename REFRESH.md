# Data Refresh Runbook

How to refresh the SEC Form 13F data behind the Shareholder Tracker website.

---

## 1. Architecture in one page

Three moving parts share **one production Postgres database**
(Cloud SQL: `shareholder-tracker:us-central1:idi-shareholder-db-prod`,
database `postgres`, user `postgres`):

```
SEC EDGAR + OpenFIGI
        │  Cloud Run jobs (backend/ Django commands, manual trigger, no scheduler)
        ▼
raw pipeline tables ──► current_investments (hand-made materialized view,
        │                pinned to ONE quarterly report date in its WHERE clause)
        │  psql \copy export to laptop
        ▼
manual/main.py  (pandas transform: renames, PRN/SH split, investor_type labels,
        │        per-security aggregation; --sec-only skips external sources)
        │  psql \copy load back, scoped by `source`
        ▼
investment table  (SEC rows + pension/NBIM rows side by side)
        │  live SQL per request — NO deploy needed for new data to appear
        ▼
Next.js app on Vercel (web/), reads via DATABASE_URL
```

Key facts:

- **The website reads only the `investment` table** (`web/app/api/investments/route.ts`).
  Its `id` is identity-generated and `document` (tsvector for search) is a stored
  generated column — the load never has to populate either.
- **Rows are partitioned by `source`.** SEC rows carry
  `source = 'U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)'`; each pension fund and
  NBIM has its own source string. A refresh replaces rows *for one source only* —
  never truncate the whole table.
- **Nothing is scheduled.** Every refresh is run by hand, job by job.
- The backend Docker image is rebuilt and pushed to Artifact Registry automatically
  on every push to `main` (`.github/workflows/deploy-image.yml`). Cloud Run jobs
  always run `:latest`, so merge pipeline changes before executing jobs.
- The Downloads page files are separate static artifacts in a **Cloudflare R2
  bucket** behind `shareholder-tracker.cdn.uchicago-dsi.org` (DSI Cloudflare
  account — not GCP), referenced from `web/config/downloads.ts`. Updating them
  is optional and independent; see [§2g](#2g-optional--downloads-page-cloudflare-r2).

### Cloud Run jobs → commands → tables

| Job (us-central1) | Django command | Writes | On critical path? |
|---|---|---|---|
| `initialize-database` | `setup.sh --migrate --load-fixtures` | DDL + `edgar_place_code` | **No** — one-time setup, never re-run |
| `scrape-bulk-submissions` | `scrape_bulk_submissions` | `scraped_company` (upsert), `scraped_form_submission`, `task` | Yes (1st) |
| `scrape-filing-detail-pages` | `scrape_filing_details` | `task` (work queue only) | Yes (2nd) |
| `scrape-investment-data` | `scrape_filing_data` | `scraped_form_13f_investment`, `scraped_form_13f_manager`, `task` | Yes (3rd) |
| `get-stock-metadata` | `get_stock_metadata` | `edgar_cusip_mapping` (via OpenFIGI) | Yes (4th) — supplies ticker/FIGI |
| `clean-stock-managers` | `clean_stock_managers` | `clean_form_13f_stock_manager` | **No** — see [Vestigial components](#7-vestigial-components) |
| `sync-materialized-view` | `sync_pgviews --force` | Django's `form_13f_stock_investment_view` | **No** — view doesn't exist in prod; see below |

All data writes except the company upsert are `bulk_create(ignore_conflicts=True)` —
**append-only and idempotent**. Re-running a failed job is safe; completed work is
skipped. Each run only processes the delta since the last refresh.

---

## 2. Prerequisites (one-time per machine)

- `gcloud` authenticated (`gcloud auth login`), project set:
  `gcloud config set project shareholder-tracker`, and ADC valid
  (`gcloud auth application-default login`).
- IAM: enough access to read Secret Manager secrets, execute Cloud Run jobs,
  and connect via Cloud SQL proxy (`roles/cloudsql.client`).
- `psql` (e.g. `brew install libpq` or postgresql).
- The Cloud SQL Auth Proxy binary at the repo root (gitignored, each person
  downloads their own — Apple Silicon shown):

  ```bash
  curl -fsSL -o cloud-sql-proxy \
    "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.25.4/cloud-sql-proxy.darwin.arm64"
  chmod +x cloud-sql-proxy
  ```

- Python 3.11+ with `pandas`, `numpy`, `duckdb`, `pyarrow`, `requests`
  for `manual/main.py`.

### Connecting to the production database

Terminal 1 (leave running):

```bash
./cloud-sql-proxy --port 5432 shareholder-tracker:us-central1:idi-shareholder-db-prod
```

Terminal 2:

```bash
export PGHOST=127.0.0.1 PGPORT=5432 PGUSER=postgres PGDATABASE=postgres
export PGPASSWORD="$(gcloud secrets versions access latest --secret=POSTGRES_PASSWORD)"
psql -c "SELECT 1;"
```

**Gotchas:**

- **The exports above are per-shell.** They must be re-run in every new terminal
  (and after closing one). If psql errors with
  `connection to server on socket "/tmp/.s.PGSQL.5432" failed`, `PGHOST` isn't
  set in that shell — psql defaulted to a local Unix socket instead of the proxy.
- **Use `PGHOST=127.0.0.1`, not `localhost`.** The proxy binds IPv4 only; on macOS
  `localhost` resolves to IPv6 `::1` first, and if *any other* Postgres is on
  port 5432 (Docker containers from unrelated projects publish on IPv6 too),
  psql will silently talk to the wrong database and fail password auth.
  Diagnose with `lsof -nP -iTCP:5432 -sTCP:LISTEN`.
- The DB password lives only in Secret Manager (`POSTGRES_PASSWORD`); there is no
  `.env` in the repo. Don't echo it.
- Jobs get credentials the same way (`secretKeyRef` in the job spec), so job
  configs are the authoritative record of env/secrets:
  `gcloud run jobs describe <job> --region us-central1 --format=export`.

---

## 3. Step 0 — verify and back up (always)

```sql
-- Source breakdown: confirms pension rows are present and gives exact strings.
SELECT source, COUNT(*) AS rows FROM investment GROUP BY source ORDER BY rows DESC;

-- Full backup (name by date). Verify the count matches the sum above.
CREATE TABLE investment_backup_YYYYMMDD AS SELECT * FROM investment;
SELECT COUNT(*) FROM investment_backup_YYYYMMDD;
```

Reference point (2026-09-01): 2,205,640 total rows — 2,165,292 SEC +
40,348 across 17 pension/NBIM sources (report date 2025-06-30).

---

## 4. Step 1 — run the scrape jobs

In order, each fully successful before the next (they feed each other
through the database):

```bash
gcloud run jobs execute scrape-bulk-submissions     --region us-central1 --wait
gcloud run jobs execute scrape-filing-detail-pages  --region us-central1 --wait
gcloud run jobs execute scrape-investment-data      --region us-central1 --wait
gcloud run jobs execute get-stock-metadata          --region us-central1 --wait
```

- Timing: job 1 ≈ hours (streams a multi-GB SEC archive); jobs 2–3 are
  EDGAR-rate-limited (10 req/s) and have historically taken **hours to days**.
  Dropping `--wait` and polling is fine — the job runs in GCP either way:

  ```bash
  gcloud run jobs executions list --job <job-name> --region us-central1 --limit 3
  ```

- Live progress from the DB (the `task` table is the pipeline's work queue
  and audit log):

  ```sql
  SELECT type, status, COUNT(*) FROM task GROUP BY type, status ORDER BY type, status;
  ```

- Logs: Console → Cloud Run → Jobs → job → Logs.
- `scrape-bulk-submissions` takes `--form_types` (default `13F-HR`) and
  `--lookback-in-days` (default 365 — filings *filed* in that window).

---

## 5. Step 2 — transform and load (laptop)

### 2a. Pin the target quarter and recreate the export view

`current_investments` is a **hand-authored materialized view** (it exists only in
the database, not in Django). Its WHERE clause pins the snapshot to one 13F
report period end. Because the date is hard-coded, `REFRESH MATERIALIZED VIEW`
is **not** sufficient after a new quarter's scrape — you must recreate it:

1. Edit the date in the marked block at the bottom of
   [`manual/sql/recreate_current_investments.sql`](manual/sql/recreate_current_investments.sql)
   (quarter ends: 03-31 / 06-30 / 09-30 / 12-31; filings are due ~45 days after).
2. Run it:

   ```bash
   psql -f manual/sql/recreate_current_investments.sql
   ```

### 2b. Regenerate the pension-fund label file (if missing)

`main.py` labels SEC filers as pension funds using `data/input/sec_pension_funds.csv`
(gitignored). It can be regenerated from prod:

```bash
psql -c "\copy (SELECT DISTINCT investor_name AS name FROM investment WHERE source = 'U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)' AND investor_type = 'PENSION FUND' ORDER BY 1) TO 'data/input/sec_pension_funds.csv' WITH (FORMAT csv, HEADER true)"
```

Review it — new pension-fund filers since the last refresh won't be in it.

### 2c. Export the SEC data

Note the join back to the base table: `main.py` needs the filing's raw
`title_class` (values like `COM CL A`), which the view does not expose.

```bash
psql -c "\copy (SELECT ci.stock_id, ci.investor_cik, ci.investor_name, ci.investor_country, ci.investor_region, ci.form_accession_number, ci.form_report_date, ci.form_filing_date, ci.stock_issuer, inv.title_class AS stock_title_class, ci.stock_cusip, ci.stock_figi, ci.stock_ticker, ci.stock_value_x1000, ci.stock_shares_prn_amt, ci.stock_prn_amt, ci.stock_voting_auth_sole, ci.stock_voting_auth_shared, ci.stock_voting_auth_none, ci.form_url FROM current_investments ci JOIN scraped_form_13f_investment inv ON inv.id = ci.stock_id) TO 'data/input/current_investments.csv' WITH (FORMAT csv, HEADER true, ENCODING 'LATIN1')"
```

Paths are relative to the **repo root**: `main.py` reads `data/input/` and
writes `data/output/` (both gitignored). If the LATIN1 export fails on an
exotic character, export without `ENCODING` and change the `ISO_8859_1`
in `main.py`'s `read_csv_auto` to UTF-8.

### 2d. Run the transform

SEC-only refresh (external pension/NBIM sources untouched — the normal mode
unless you have fresh external files):

```bash
cd manual && python main.py --sec-only
```

Output: `data/output/shareholder_tracker_release_YYYYMMDD.{csv,parquet,sqlite}`.
The CSV is pipe-delimited with `NULL` for nulls, and its 37 columns match the
`investment` table (minus generated `id`/`document`) in order.

`--last-accessed-date YYYY-MM-DD` overrides the `last_accessed_date` column
(defaults to today, UTC).

For a **full refresh** including external sources: drop `--sec-only` and supply
`data/input/` with the NBIM export CSV, the pension funds `.xlsx`, and
`currency_country_map.json` (filenames are hard-coded near the top of `main()` —
update them, along with the NBIM `document_report_date` constant in
`_process_nbim_investments`).

### 2e. Load, scoped by source

Inside one transaction so a failed load rolls back cleanly:

```sql
BEGIN;
DELETE FROM investment WHERE source = 'U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)';
\copy investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date) FROM 'data/output/shareholder_tracker_release_YYYYMMDD.csv' WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL');
COMMIT;
```

Pension/NBIM rows are untouched — they carry different `source` values and are
never aggregated together with SEC rows (`source` is a group-by key in the merge).

### 2f. Verify

```sql
SELECT source, COUNT(*) AS rows FROM investment GROUP BY source ORDER BY rows DESC;
```

Pension counts must equal Step 0 exactly; SEC count should look plausible for
the quarter. Spot-check the website immediately — it reads this table live, so
new data (or a mistake) is user-visible the moment `COMMIT` succeeds.

**Rollback:** `BEGIN; DELETE FROM investment; INSERT INTO investment SELECT *
FROM investment_backup_YYYYMMDD; COMMIT;` (or scoped by source). Drop old
backup tables once confident.

### 2g. Optional — Downloads page (Cloudflare R2)

The Downloads page (`web/app/downloads/page.tsx`) links to static release files
served from a **Cloudflare R2 bucket** on the custom domain
`shareholder-tracker.cdn.uchicago-dsi.org`. The bucket lives in the DSI
Cloudflare account that owns the `uchicago-dsi.org` zone — **not** in the GCP
project — and nothing in this repo or its CI touches it: uploads are done by
hand (Cloudflare dashboard or `wrangler r2 object put`). Ask a DSI Cloudflare
admin for access. Objects are laid out one dated prefix per release:

```
<bucket>/YYYY-MM-DD/shareholder_tracker_release_YYYYMMDD.zip         (zipped CSV)
<bucket>/YYYY-MM-DD/shareholder_tracker_release_YYYYMMDD.parquet
<bucket>/YYYY-MM-DD/shareholder_tracker_release_YYYYMMDD.sqlite.gz   (gzipped SQLite)
<bucket>/YYYY-MM-DD/shareholder_tracker_data_dictionary_YYYYMMDD.pdf
```

1. **Build the release from prod, not from `main.py`.** A `--sec-only` run has
   no pension rows, and a full run needs pension inputs that no longer exist.
   The `investment` table is exactly what the site serves, so export it
   (proxy running and `PG*` variables set, per §2):

   ```bash
   python manual/export_release.py --release-date YYYY-MM-DD
   ```

   This writes `data/output/YYYY-MM-DD/` with the CSV, `.zip`, `.parquet`,
   `.sqlite`, and `.sqlite.gz` (Parquet column types match the December 2025
   release) and prints per-source row counts plus file sizes. The counts must
   match §2f exactly. `--csv <path>` reuses an existing export instead of
   querying prod.

   *Precision caveat.* The `investment` table stores its numeric columns at
   fixed scales — `numeric(6,5)` for the conversion rate and the two percentage
   columns, `numeric(20,2)` for the amounts — so every load rounds to 5 or 2
   decimals. A release exported from prod therefore differs from the December
   2025 parquet (which `main.py` wrote at full float precision) in those columns
   only: pension conversion rates by ≤ 4.3e-6, and 22 ABP
   `security_market_value_amount` values in the second decimal (e.g. 8.235 →
   8.24). `security_market_value_amount_usd` is computed before the load and is
   unaffected. These rounded values are what the website shows, so the download
   now matches the site exactly (verified 2026-09-08: all 1,932,680 SEC rows and
   every text/integer pension column identical to their sources).
2. **Upload** the `.zip`, `.parquet`, and `.sqlite.gz` to the bucket under the
   `YYYY-MM-DD/` prefix. In the Cloudflare dashboard: switch to the DSI account
   (the one listing `uchicago-dsi.org` under *Websites*) → **R2 Object Storage**
   → the bucket whose *Settings → Custom Domains* shows
   `shareholder-tracker.cdn.uchicago-dsi.org` → *Create folder* `YYYY-MM-DD` →
   upload the three files into it. Or, with `wrangler` logged in to that
   account (`npx wrangler login`; `npx wrangler r2 bucket list` shows the
   bucket name):

   ```bash
   npx wrangler r2 object put <bucket>/YYYY-MM-DD/<file> --file data/output/YYYY-MM-DD/<file> --remote
   ```

   `--remote` is required — without it wrangler writes to a local simulation of
   the bucket and reports success. Before touching the web app, confirm each
   object is live and the size matches the local file:

   ```bash
   curl -sI https://shareholder-tracker.cdn.uchicago-dsi.org/YYYY-MM-DD/<file> | grep -iE '^HTTP|content-length'
   ```
3. **Data dictionary.** The release schema has not changed since December 2025,
   so point the new entry at that PDF's existing URL
   (`…/2025-12-18/shareholder_tracker_data_dictionary_20251218.pdf`) instead of
   uploading a copy. That PDF has known defects that predate this refresh — it
   lists `id`, omits `document_filing_date`/`investor_abbreviation`/`text`, and
   names the voting-authority fields `stock_percent_voting_auth_*` rather than
   `stock_voting_auth_*` — fix them whenever the schema next changes.
4. **Publish.** Add an entry at the *top* of `DOWNLOAD_CONFIG` in
   `web/config/downloads.ts` (date, dictionary URL, and the three file URLs
   with sizes as printed by the script), open a PR — the Vercel preview lets you
   click every link — and merge to `main`. Vercel deploys production from
   `main`; the config is a static import, so there is no cache to bust.

---

## 6. Quarter-pinned values — the per-refresh checklist

These are hard-coded and must be updated each refresh:

- [ ] `manual/sql/recreate_current_investments.sql` — `WHERE form_report_date = '…'`
- [ ] (full refresh only) NBIM `document_report_date` constant in `main.py`
- [ ] (full refresh only) input filenames at the top of `main()`
- [ ] `last_accessed_date` — defaults to today via `--last-accessed-date`
- [ ] (downloads only) new `YYYY-MM-DD/` prefix in R2 and a new entry at the top
      of `web/config/downloads.ts` (§2g)

Also worth doing once: the Cloud Run jobs' `EDGAR_API_USER_AGENT` still names the
departed operator's email. SEC expects a working contact — update the env var on
each job config.

---

## 7. Vestigial components (verified 2026-09-01)

Documented so nobody spends an afternoon on them again:

- **`clean-stock-managers` job / `clean_form_13f_stock_manager` table** — parses
  the "other managers" free-text on each holding into names. Its only consumer
  was the "investor aliases" feature, removed from `main.py` and the web app in
  commit `951780b` (Jan 2026). Not on the critical path; last execution
  (Sept 2025) failed — likely memory (it loads all stock ids into Python sets).
- **`sync-materialized-view` job / Django's `Form13FStockInvestmentView`** — the
  Django-defined materialized view does **not exist** in the production database
  (only the hand-made `current_investments` does). The job ran once at setup in
  March 2025. Executing it would recreate the Django view; harmless but unused.
- **`initialize-database` job** — one-time setup (migrations + place-code
  fixture). Never re-run against a populated database.

## 8. Improvement ideas (discussed, not implemented)

- **Read filing documents from the `idi-sec-scraper` S3 bucket** instead of live
  EDGAR in jobs 2–3, bypassing the 10 req/s limit. Coverage confirmed compatible
  (the bucket stores `index.htm`, the HTML information table, and the primary
  doc for 13F-HR). Requires: a fetch abstraction with EDGAR fallback, AWS
  read-only creds via Secret Manager, and a bucket-coverage validation pass.
  Estimated 2–3 days; worthwhile if refreshes recur quarterly.
- Automate the whole refresh (Cloud Scheduler + a job for the export/transform/
  load layer) so it stops being a hand-run, laptop-dependent process.
