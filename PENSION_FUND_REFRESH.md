# Pension Fund Data Refresh Runbook

How pension fund (and NBIM) data gets into the Shareholder Tracker, and the plan
for incorporating the new June 2026 workbook. Companion to [REFRESH.md](REFRESH.md)
(SEC refresh), which covers shared setup: database connection, backups, and load
mechanics.

**Status (2026-09-01):** the code in `manual/main.py` reads the *old* workbook
format ("Pension Fund for Shareholder Tracker", tabs named `Copy of <x>`). The
new workbook ("Pension Funds for Shareholder Tracker 2026-06-11") is a format
break — Sections 3–4 below are the work required before it can be loaded.
Sections 1–2 describe behavior as it exists today.

---

## 1. How pension data works today

- Pension rows live in the same `investment` table as SEC rows, distinguished by
  `source` (one string per fund, e.g. `PENSIOENFONDS ZORG EN WELZIJN`,
  `NORGES BANK`). The website treats all rows identically.
- Input is a single Excel workbook, **one tab per disclosure document** (a fund
  can span several tabs, e.g. AP3 × 3). `_process_pension_funds` in
  `manual/main.py` concatenates all tabs, then keys **three hardcoded dicts off
  the tab names** to assign the source string, disclosure URL, and abbreviation.
- **NBIM is not in the workbook.** It has its own branch
  (`_process_nbim_investments`) reading a CSV exported from nbim.no, with
  hardcoded report date, USD values, and Norway metadata.
- **There is no date filtering** on pension data. Whatever report date each tab
  carries is loaded as-is (dates currently span 2023-12 to 2025-10). Only the
  SEC side is quarter-pinned (via the `current_investments` view's WHERE clause).
- **There is no deduplication across sources.** The merge groups by `source`,
  so the same real-world holding can legitimately appear under two sources.
  Known live case: Norges Bank files a 13F, so its US holdings appear under the
  SEC source *and* its global holdings under `NORGES BANK`. Any US public
  pension added via the workbook (e.g. LACERA) that also files a 13F will be
  double-represented unless explicitly handled.
- Funds currently **excluded in code** as "not properly verified"
  (`excluded_sources`): Pensioenfonds Detailhandel, PMT pensioenfonds,
  Pensioenfonds Rail & OV.
- Currency conversion: `manual/currency.py` fetches annual USD rates from the
  IMF's public SDMX API, using `data/input/currency_country_map.json`
  (currency code → IMF area code; euro area is `G163`). The file is gitignored
  and was lost with the original operator — it must be rebuilt (Section 4).

## 2. The new workbook (June 2026) — what changed

Owner: IDI's pension-data contact at Warren Wilson College. 21 tabs, ~54k data rows.

Improvements over the old format:
- **One tab per fund**, plainly named (`PME`, `PKA`, `AP3`, …) — AP2/AP3/AP4's
  multi-tab splits are consolidated.
- **`Data Source URL` column on every row** — replaces the hardcoded `url_map`
  (where stale disclosure links currently live).
- **`NBIM` is now a tab** (7,201 rows, NOK, 2025-12-31) — candidate to replace
  the separate CSV branch (8,374 rows, USD — scopes differ, reconcile first).
- **`LACERA` is new** (12,585 rows, USD, 2025-09-30) — first US fund in the
  workbook.
- Fresher report dates: mostly 2025-12-31, several 2026 (PKA 2026-05-31,
  PME 2026-04-30, Detailhandel/PMT 2026-03-31).

Why the current code can't read it: every tab-name key misses (NaN `source` for
all rows), two expected headers exist nowhere (`BB Ticker`,
`Private Equity - Vintage Year`) causing an immediate KeyError, per-tab header
drift, and a new `x100` multiplier the converter doesn't know.

## 3. Spreadsheet fixes to request (data team)

**Blockers — cannot be safely coded around:**

1. **AP2**: remove the embedded second header at ~row 1150 and re-align the rows
   below it — the tab has two different column layouts under one header row
   (~800 rows have values under the wrong columns).
2. **ZORG & WELZJIN**: fix the misspelling → "Welzijn" in the tab name, the
   `Shareholder` cells, and the SOURCES row (this string becomes the public
   `source` label); re-align the ~234-row private-equity block whose URL sits in
   an unnamed 9th column; delete ~180 blank tail rows; rename header
   `Shareholder` → `Shareholder - Name`.
3. **AP4**: `Issuer - Country Name` contains 2-letter codes — rename the header
   to `Issuer - Country Code` or fill in names.
4. **DANICA**: report dates are `31-12-2025` text strings — convert to real
   dates; rename `Report Date URL` → `Data Source URL`.

**Should fix (cheap in the sheet; otherwise code special-cases):**

5. Header consistency: `Security - Market Value` → `… - Amount` (AP3/AP4/AP7);
   `Security - Market Value - Currency` → `… Currency Code` (NBIM);
   `Private Equity - Vintage year` → `… Year` (AP3).
6. **AP7 `Stock - Exchange`** contains numbers that look like share prices —
   clarify, rename, or drop the column.
7. Store numbers as numbers (currently: `64 895` space-grouped text,
   `6.111.849,14` EU format, `0,05 %` percent strings).

**Decisions to confirm:**

8. Detailhandel's 36 `Sanctionized` rows — include or drop?
9. KPA has no market-value data (names + dates only) — intentional?
10. BPL is still 2023-12-31 — no newer disclosure?
11. Detailhandel, PMT, Rail & OV were code-excluded as unverified — now vetted?
12. NBIM: does the tab replace the CSV branch? (Row counts and currency differ.)
13. LACERA: confirm whether it also files a 13F already captured in the SEC
    data (double-count risk). Check once SEC refresh lands:
    `SELECT COUNT(*) FROM investment WHERE source LIKE 'U.S.%' AND investor_name LIKE '%LOS ANGELES%';`

## 4. Code changes required (`manual/`)

1. **Rewrite `_process_pension_funds`** for the new contract:
   - Read every tab except `SOURCES`; normalize headers per tab (strip, apply a
     canonical-rename map for the Section 3.5 variants, add missing canonical
     columns as empty).
   - Replace the three tab-name dicts with one fund-metadata map keyed on the
     **new** tab names (source string, abbreviation, investor country/region);
     take URLs from the per-row `Data Source URL` column.
   - Add `LACERA` (and `NBIM`, per decision 12) to the metadata map.
   - Robust parsing: space/dot thousands separators, comma decimals, `%`
     strings, letter-prefixed share counts (drop), Danica date format.
   - Extend the multiplier map with **`x100`** (bpfBOUW) — today a KeyError.
   - Update/remove `excluded_sources` per decision 11.
2. **Add `--pension-only`** to `main()` (inverse of `--sec-only`: skip SEC
   processing, feed empty frames to the merge) and **parameterize the input
   filename** (currently hardcoded).
3. **Rebuild `data/input/currency_country_map.json`** for the ~40 currencies
   now present (AP7 alone uses 36) and commit it to the repo.
4. **Dry-run** against a downloaded copy of the workbook before any prod run
   (same harness as the SEC-only dry run): per-tab rows in vs. rows out, null
   rates, spot-checked USD conversions.
5. Update this file and REFRESH.md when implemented.

Estimate: 2–3 days once the sheet fixes land.

## 5. Refresh steps (once sheet + code are ready)

Prereqs per [REFRESH.md](REFRESH.md) § 2: proxy running, `PGHOST=127.0.0.1`,
password from Secret Manager. Run this *separately* from a SEC refresh so each
load verifies in isolation.

1. **Download the Google Sheet as `.xlsx`** into `data/input/`.
2. **Verify + back up** (REFRESH.md § 3): record the current pension source
   strings and per-source counts; create and count a dated backup table.
3. **Transform:**

   ```bash
   cd manual && python main.py --pension-only
   ```

   → `data/output/shareholder_tracker_release_YYYYMMDD.csv` (pension/NBIM rows
   only).
4. **Validate locally before touching prod**: per-source CSV row counts vs. tab
   row counts (minus documented drops); no null `source`/`url`; USD conversions
   in plausible ranges.
5. **Load in one transaction** — the inverse of the SEC load. The DELETE must
   list the **old source strings currently in prod** (from step 2), not the new
   ones — funds get renamed (e.g. the Welzijn spelling fix), and NBIM's string
   is `NORGES BANK`:

   ```sql
   BEGIN;
   DELETE FROM investment WHERE source IN (
     -- every pension/NBIM source string from step 2 that this load replaces
     'NORGES BANK', 'PENSIOENFONDS ZORG EN WELZIJN' /* , ... */ );
   \copy investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date) FROM 'data/output/shareholder_tracker_release_YYYYMMDD.csv' WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL');
   COMMIT;
   ```

   If a fund currently in prod is *absent* from the new data, decide explicitly:
   keep its old rows (omit from the DELETE) or retire it (include it).
6. **Verify**: rerun the `GROUP BY source` breakdown — the SEC count must be
   unchanged; old pension strings gone; new strings (LACERA, corrected Welzijn)
   present with expected counts. The website reflects the change immediately.
7. **Optional, later**: regenerate the combined release for the Downloads page
   from prod with `python manual/export_release.py` (REFRESH.md § 2g) —
   per-source `main.py` runs are not complete snapshots.

## 6. Known caveats

- **Mixed vintages by design**: pension report dates (2023-12 → 2026-05) sit
  alongside quarter-pinned SEC data. Each row carries `document_report_date`,
  so it's visible, but it's an editorial choice the team owns.
- **No cross-source dedup exists** (see § 1). NBIM/SEC overlap is live today;
  LACERA may add another. If dedup is ever wanted, it's new logic, not a
  regression fix.
- The workbook copies analyzed for this plan (full exports, 2026-09-01) are
  session artifacts; re-download fresh copies for any real run.
