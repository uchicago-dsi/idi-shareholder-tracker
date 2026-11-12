# Pension Fund Data Refresh Runbook

How pension fund and NBIM (Norges Bank) data gets into the Shareholder Tracker,
and the plan for loading the 2026 workbook. Companion to [REFRESH.md](REFRESH.md)
(SEC refresh), which covers shared setup: database connection, backups, and load
mechanics.

Three independent pieces of work, each replacing only its own `source` rows:

| Piece | Input | Section | Status (2026-11-10) |
|---|---|---|---|
| NBIM | CSV downloaded from nbim.no | § 5 | **Loaded to prod 2026-11-10** (2026-06-30 snapshot, 7,077 rows) |
| Pension workbook | Google Sheet → `.xlsx` | §§ 2–4, 6 | **Loaded to prod 2026-11-10** (27,114 rows, 15 funds) |
| SEC-side relabel (PGGM, APG ×2) | one `UPDATE` in prod | § 6a | **Done 2026-11-10** (§ 8.2) |
| BPL ownership-field correction | one `UPDATE` in prod | § 6a | **Parked** (decision 2026-11-10, commit d3e16ce): not partner-requested; prod BPL values unchanged. Raise with the PKA question. |
| Downloads page release | `export_release.py` → R2 → `downloads.ts` | § 8.6 | Export built and validated 2026-11-10; R2 upload + PR merge pending |
| About page | `web/app/about/page.tsx` | § 6b / § 8.7 | Edited on the branch; PR merge pending |

**§ 8 is the ordered prod run sheet. § 8.0–8.5 were executed on 2026-11-10 and
the § 8.5 table matched exactly: 21 sources, 1,980,171 rows.**

Everything below reflects the sheet as re-downloaded on 2026-11-10 and the code
on branch `issue-17-data-refresh`. Pending re-scrapes from the data team:
Sampension (frozen on its 2025-08-31 rows) and AP4 (loaded without market
values); each is a single-source reload when the corrected tab arrives.

---

## 1. How pension data works today

- Pension rows live in the same `investment` table as SEC rows, distinguished by
  `source` (one string per fund, e.g. `PENSIOENFONDS ZORG EN WELZIJN`,
  `NORGES BANK`). The website treats all rows identically. Prod holds 17
  pension/NBIM sources, 40,348 rows, all loaded 2025-12-18 (`last_accessed_date`).
- Input is a single Excel workbook. `_process_pension_funds` in `manual/main.py`
  concatenates every tab, drops rows with no `Shareholder - Name`, and then keys
  **four hardcoded dicts off the tab names** (`Copy of AMF`, `Copy of ap2
  foreignequity`, …) to assign the `source` string, abbreviation, investor
  country, and disclosure URL. `investor_name` is taken from the sheet's
  `Shareholder - Name` cell, uppercased.
- Hardcoded cleaning in that function, all keyed on the *old* tab names or old
  data quirks: three excluded issuer strings, a `CORPORATE BOND` type filter, an
  `excluded_sources` list (Detailhandel, PMT, Rail & OV — "not properly
  verified"), per-tab space/dot stripping of amounts, a `FUND EQ` → `Equity
  Fund` type rule, an AP3 private-equity tab rule, and a Dutch→English country
  name map.
- Market value → USD: `manual/currency.py` fetches IMF exchange rates (annual
  average by year of `document_report_date`; falls back to the mean of the
  available monthly rates for that year). Currency codes are mapped to IMF area
  codes via `data/input/currency_country_map.json` — **gitignored and missing**
  on this machine (§ 4.3). Multipliers `x1` / `x1_000` / `x1_000_000` are
  applied after conversion; an unknown multiplier string is a `KeyError`; a blank
  one means `x1`.
- **NBIM is not loaded from the workbook.** It has its own branch
  (`_process_nbim_investments`) reading a CSV downloaded from nbim.no. The
  rows in prod today (8,374, report date 2025-06-30) are the nbim.no **Equity**
  list for H1 2025 and nothing else. Details and refresh steps in § 5.
- **There is no date filtering** on pension data. Whatever report date each tab
  carries is loaded as-is. Only the SEC side is quarter-pinned.
- **There is no deduplication across sources.** The merge groups by `source`.
  NBIM is *not* a live overlap case (checked 2026-09-09 against the 2026-06-30
  SEC quarter: zero SEC rows carry a Norges Bank investor name); the dead
  `investor_abbreviation = "NBIM"` special case in `_process_sec_investments`
  was removed 2026-11-10 (§ 5b). LACERA does not file a 13F either (§ 6a). PGGM and APG *do*, and
  are handled on the SEC side only (§ 6a).
- Two funds in prod have **no market values at all** (name + date only): AMF
  (298 rows) and KPA (548 rows). That is the established norm for them, not a
  defect; the new sheet is the same.
- Known prod data-quality debts inherited from the 2025-12 load, relevant
  because the new sheet has the same traits: AP2 is split across two
  abbreviations (`AP2` 1,152 rows + `P2` 131 rows — two old tabs); PKA's and
  AP7's `stock_percent_ownership` values are actually **portfolio weights**, not
  ownership stakes (e.g. PKA / Apple = 0.53).

## 2. The workbook (2026-09-09 copy)

Owner: IDI's pension-data contact at Warren Wilson College. Live copy:
<https://docs.google.com/spreadsheets/d/1Bb3ykH3jNb1WFHMtP9FYdpulQkAQP_6bmP_Fguf-f2I>.
Download as `.xlsx` via `File → Download`, or
`https://docs.google.com/spreadsheets/d/1Bb3ykH3jNb1WFHMtP9FYdpulQkAQP_6bmP_Fguf-f2I/export?format=xlsx`.

Layout: a `SOURCES` tab (fund, file date, link — informational only; it still
lists BPL, ZORG&WELZJIN, DETAILHANDEL, SAMPENSION and NBIM, which have no tabs,
so **do not key code off it**) plus **15 fund tabs, one per fund, every one
suffixed `(checked)`**. ~31k data rows, no blank tail rows, no embedded second
headers, `Data Source URL` filled on every row of every tab (Danica calls it
`Report Date URL`). The `SAMPENSION (checked)` tab was deleted by the data team
on 2026-11-10 pending a re-scrape (§ 3.3).

| Tab | Rows | Report date | Value column · currency · multiplier | Other columns | Notes |
|---|---|---|---|---|---|
| `AMF (checked)` | 344 | 2025-12-31 | **none** | Type (`Foreign Stock` / `Swedish Stock` / `Private Swedish Stock`) | names only, as in prod |
| `AP2 (checked)` | 1,289 | 2025-12-31 | Amount · SEK · `x1_000` | Country Code, ISIN | 1,185 amounts are space-grouped text (`1 146 640`) |
| `AP3 (checked)` | 1,078 | 2025-12-31 | `Security - Market Value` · SEK · `x1_000` | ISIN, Ticker | 139 rows are private-equity funds with no ISIN/value; 22 ISINs have the next issuer's name glued on (`CH0011075394NOVARTIS`) |
| `AP4 (checked)` | 1,306 | 2025-12-31 | **none** | `Issuer - Country Name` (holds 2-letter codes), ISIN, Shares (space-grouped text), % Ownership, % Voting (155 rows) | prod had SEK market values; load as-is per data team, values return after a re-scrape — § 3.4 |
| `AP7 (checked)` | 1,919 | 2025-12-31 | `Security - Market Value` · SEK · `x1` | `Stock - Exchange` (local share price), Shares | currency fixed to SEK and the weight column removed on 2026-11-10 (§ 3.1, § 3.5) |
| `BPFBOUW (checked)` | 4,228 | 2025-12-31 | Amount · EUR · **`x1_00`** (typo for `x100`) | — | § 3.2; 3 country-subtotal rows still present |
| `DANICA (checked)` | 2,392 | 2025-12-31 | Amount · DKK · `x1_000_000` | — | dates are `31-12-2025` strings; URL header is `Report Date URL` |
| `KPA (checked)` | 552 | 2026-02-26 | **none** | — | names only, as in prod; one cell reads `KPA Pension Pension` |
| `LACERA (checked)` | 9,714 | 2025-09-30 | Amount · USD (blank on 7,322 rows) · (none → `x1`) | Type (`EQUITY`), ISIN | 109 rows have name fragments in the ISIN column, 10 blank issuer names |
| `PENSION DANMARK (checked)` | 1,593 | 2025-12-31 | Amount · EUR · `x1_000_000` | Country Name, Sector | clean |
| `PKA (checked)` | 1,660 | 2026-05-31 | Amount · DKK · (none → `x1`) | ISIN, % Ownership as `0,04 %` text | % column is portfolio weight, § 3.5 |
| `PME (checked)` | 1,363 | 2026-04-30 | Amount · EUR · (none → `x1`) | Country Name, Sector | clean |
| `PMT (checked)` | 1,384 | 2026-03-31 | Amount · EUR · (none → `x1`) | — | clean; new to prod (decision 11) |
| `RAILOV (checked)` | 1,054 | 2025-03-31 | Amount · EUR · (none → `x1`) | — | clean; new to prod (decision 11) |
| `VERVOER (checked)` | 1,275 | 2025-12-31 | Amount · EUR · `x1_000` (added 2026-11-10) | — | 5 exact duplicate rows remain |

Not in the workbook: BPL, PFZW, ABP, Sampension (keep prod rows — § 6a),
Detailhandel (excluded — § 6a), NBIM (nbim.no — § 5).

Compared with the 2026-09-01 copy the earlier analysis was based on: AP2's
embedded second header is gone, the ZORG&WELZJIN tab is gone, the `x100`
multiplier is gone (replaced by an apparently wrong `x1_000`), and blank tail
rows are gone. Everything else below was re-verified on the current file.

## 3. Sheet issues raised with the data team

Found on the 2026-09-09 download; answered by the data team and re-verified on
the 2026-11-10 download. Numbered for reference from § 4. Resolution notes are
marked **→**.

**Blockers — wrong data would load:**

1. ~~**AP7 — currency column holds the share's trading currency, values are SEK.**~~
   `Security - Market Value` ÷ `Stock - Number of Shares` equals `Stock -
   Exchange` × the SEK rate of the stated currency for every row (Nvidia:
   64,869,888,109 / 37,619,588 = 1,724 SEK ≈ 187.54 USD × 9.2). So `Stock -
   Exchange` is the local share price and the values are whole SEK (tab total
   1,320 bn SEK ≈ $134 bn, matching AP7's size and the SEK values in prod).
   Ask: set `Security - Market Value - Currency Code` to `SEK` on every row and
   rename `Stock - Exchange` → `Stock - Price (local currency)` or drop it.
   Until fixed, converting with the stated codes would inflate AP7 ~10×.
   **→ Resolved 2026-11-10.** Currency set to `SEK` on all 1,919 rows (the
   per-stock currency on AP7's site is the trading currency; the table is in
   SEK). `Stock - Exchange` still holds the local share price — code ignores
   it.
2. ~~**bpfBOUW — multiplier `x1_000` is 10× too large; should be `x100`.**~~ Nvidia
   is 6,096,263 → €6.1 bn under `x1_000`, vs €0.64 bn in prod (2025-06-30,
   `635,953.9 × 1,000`). Tab total is €143 bn under `x1_000` (bpfBOUW's *entire*
   fund is ~€75 bn) and €14.3 bn under `x100` (prod: $19 bn). The 2026-09-01
   copy of the sheet said `x100`. Ask them to confirm the PDF's unit and set the
   multiplier accordingly. Also remove the 3 **country subtotal rows** that
   came through as issuers: `Hong Kong` (971,182), `Saoedi-Arabië` (426,589),
   `Zuid Korea` (4,353,216).
   **→ Resolved 2026-11-10, with a typo.** The fund reports to a tenth of a
   euro, so `x100` is right. The sheet now says **`x1_00`** on every row — code
   must accept that spelling (§ 4.2.5) or the team must correct it. The three
   country-subtotal rows are **still present** — code drops them (§ 4.2.2).
3. ~~**Sampension — ISINs are shifted against issuer names on roughly rows~~
   280–800.** Cross-checking against PKA's and LACERA's ISINs: `CRH PLC` carries
   CrowdStrike's ISIN, `CROWDSTRIKE HOLDINGS` carries Crown Castle's, `NUTRIEN
   LTD` carries Nvidia's, `KEYENCE CORP` carries Keysight's, `HP INC` carries
   HSBC's. ~370 of 838 checkable rows mismatch, concentrated in the middle of
   the tab; the first ~280 and last ~270 rows are fine. Prod's Sampension ISINs
   (2025-08-31 load) were correct, so this is a transcription error in the new
   tab. 58 further ISINs are OCR-damaged (`DEQOOA1EWWWO`, `US00724F 1012`).
   Ask them to re-extract the ISIN column. Loading as-is would attach wrong
   identifiers to ~300 holdings. ISINs are shown on every result card and are
   searchable, but drive no totals or filters, so if the fix is slow the
   fallback is to **load Sampension with ISINs blanked** (whole tab, or the
   affected block) — the rows then behave like the Dutch funds that never had
   ISINs. Alternative: hold Sampension on its prod rows (2025-08-31, correct
   ISINs). State which.
   **→ Resolved 2026-11-10: tab deleted.** On inspection the market values had
   shifted too, not just the ISINs. The team will re-scrape; until then
   **Sampension keeps its prod rows** (1,181 rows, 2025-08-31) — it moves to
   the "keep" list in § 6a and out of the DELETE.
4. ~~**AP4 — market values were dropped.**~~ Prod AP4 rows carry SEK values
   (`x1_000_000`, $24.7 bn total); the new tab has only share counts and
   percentages. AP4's holdings report does publish values. Ask for a
   `Security - Market Value - Amount` / `Currency Code` / `Multiplier` set; if
   they can't, accept that AP4 becomes a names-and-shares fund like AMF/KPA
   (decide explicitly — it removes $24.7 bn from the Tracker's totals).
   **→ Decided 2026-11-10: load as-is.** The scraped values had shifted rows
   and could not be repaired, so the team dropped them deliberately. AP4
   loads with names, ISINs, share counts and (155 rows) ownership/voting; no
   market value or USD. The Tracker's pension total drops by ~$24.7 bn until
   the students re-scrape AP4 with values. Accepted.
5. **PKA and AP7 — `Stock - Percent Ownership` is portfolio weight, not
   ownership.** PKA / Nvidia = `6,15 %` (5.03 bn DKK of an 81.9 bn DKK tab);
   AP7 / Nvidia = 0.0474 (64.9 bn of 1,320 bn SEK). The website renders this
   field as the sentence *"The investor's shares give it X% ownership"*, so a
   weight loaded here is a false statement on every card. Ask them to rename
   the column (`Portfolio Weight`) or drop it. Code will **not** map it for
   these two tabs regardless (§ 4). Only AP4's column (and AP2/AP3 in prod) is
   a real ownership stake — their top values are small Swedish companies with
   a matching voting-power figure; PKA/AP7/BPL/Danica top out on Apple, Nvidia
   and Microsoft, which is the signature of a weight. Ask the team to state,
   for every fund that reports a percentage, which of the two it is.
   *Prod today:* PKA (2,571 rows), AP7 (2,072), **BPL (1,148)** and Danica (482)
   all carry weights in this field. PKA/AP7/Danica are replaced by the load;
   BPL is a "keep" fund, so its values survive the refresh; **left as-is
   pending partner confirmation** — see § 6a.
   **→ AP7 resolved 2026-11-10:** the team agreed and deleted the column.
   **→ PKA still open — the team disagrees, but the sheet does not support
   their reading.** They cite "DKK 111,123,771 of Adidas = a 0.04 % stake".
   On the 2026-11-10 sheet PKA's Adidas row is **DKK 30,032,619**, and
   30.0 m / 81.9 bn (the tab total) = 0.037 % → `0,04 %`. Testing every row:
   **all 1,660 PKA percentages equal the row's share of the tab total to
   within rounding.** The top of the column is Nvidia 6.15 %, Apple 5.29 %,
   Microsoft 3.81 % — PKA does not own 6 % of Nvidia (that would be ~$270 bn
   against an $12 bn equity book). A real stake in Adidas of 0.04 % would
   also be *coincidentally* similar, which is likely what misled them. Reply
   with this evidence and ask them to delete the PKA column as they did for
   AP7. **Code does not map it regardless.**
6. ~~**Vervoer — multiplier missing; values are thousands of EUR.**~~ Nvidia
   435,481 vs prod 353,689 `x1_000`; whole fund ≈ €11 bn under `x1_000`, €11 m
   under `x1`. Ask for a `Security - Market Value - Multiplier` column set to
   `x1_000`. Also 5 exact duplicate rows (e.g. NVIDIA Corp twice) — code will
   drop exact duplicates, but the sheet should not have them.
   **→ Resolved 2026-11-10.** `Security - Market Value - Multiplier = x1_000`
   on all 1,275 rows. The 5 duplicate rows remain — code drops them.
7. **LACERA** (a) `Security - Market Value - Currency Code` blank on 7,322 of
   9,714 rows (all non-US ISINs; the amounts are USD-scale) — fill `USD` or
   confirm, code will default LACERA to USD; (b) 109 rows where a multi-word
   issuer name spilled into the ISIN column (`MALLINCKRO` / `CONTRA`,
   `SOFTWARE CORPORATION` / `AQ`) and 10 rows with a blank issuer name — these
   are mostly private/unlisted positions; ask them to fix the names and blank
   the ISIN.
   **→ Not answered 2026-11-10.** Not blocking: code defaults LACERA's currency
   to USD and blanks malformed ISINs (§ 4.2). Re-raise with the re-scrape
   requests for Sampension and AP4.

**Should fix (cheap in the sheet; otherwise code special-cases). None were
addressed on 2026-11-10; code handles all of them (§ 4.2), so they are not
blocking:**

8. Header consistency: `Security - Market Value` → `Security - Market Value -
   Amount` (AP3, AP7); `Report Date URL` → `Data Source URL` (Danica);
   `Issuer - Country Name` → `Issuer - Country Code` (AP4 — the cells are
   2-letter codes).
9. Danica report dates are `31-12-2025` text — make them real dates.
10. Numbers stored as text: AP2 amounts and AP4 share counts are space-grouped
    (`1 146 640`); 45 Sampension amounts have a stray internal space
    (`44 885713` = 44,885,713); PKA percentages are `0,04 %` strings.
11. AP3: add `Security - Type` (139 private-equity rows have no ISIN/value and
    are only identifiable by that) and, if available, vintage year — prod's 151
    AP3 `PRIVATE EQUITY FUND` rows all had one.
12. KPA: fix the single `KPA Pension Pension` cell. Confirm the report date
    (2026-02-26 looks like a publication date, not a holdings date).
13. AP3: 22 ISIN cells have the next row's issuer name appended — code will
    truncate to 12 characters, but the sheet should be fixed.

**Decisions (state as of 2026-09-09):**

- ~~Detailhandel's `Sanctionized` rows~~ — **moot**, tab removed (§ 6a).
- ~~KPA has no market-value data — intentional?~~ — **yes**, same as prod
  (as is AMF). Loads as names + dates.
- ~~BPL still 2023-12-31~~ — **resolved**, keep prod rows (§ 6a).
- **Open — decision 11:** PMT and Rail & OV were `excluded_sources` in the old
  code as "not properly verified". Both now have `(checked)` tabs and both are
  named in the new About-page text (§ 6b), which implies they load. **Confirm
  with the data team that `(checked)` means cleared**, then remove them from
  the exclusion list.
- ~~NBIM tab replaces CSV branch?~~ — **no**, nbim.no (§ 5); no NBIM tab exists
  anyway.
- ~~LACERA files a 13F?~~ — **no** (§ 6a). No double-count.
- ~~APG Asset Management US Inc. relabel~~ — **yes** (2026-11-10): relabel all
  three filers (§ 6a).
- **Parked — PKA percentage column** (§ 3.5): team believes it is ownership;
  the data says weight. Decision 2026-11-10: **ignore the column for now**
  (code does not map it) while this is settled with the partner. Not blocking.
- ~~NBIM snapshot date~~ — **newest available** (2026-11-10). At the time of
  writing that is 2026-06-30 (7,077 rows); § 5c step 1 picks it up
  automatically.
- **Public labels for new funds — proceeding with the § 4.1 proposal** unless
  told otherwise: `PENSIOENFONDS METAAL EN TECHNIEK`, `PENSIOENFONDS RAIL & OV`,
  `LOS ANGELES COUNTY EMPLOYEES RETIREMENT ASSOCIATION`; existing funds keep
  their current strings. Changing a label later means a DELETE/reload of that
  one fund — cheap, so this is not blocking.
- ~~Sampension fallback~~ — **keep prod rows**; tab deleted pending re-scrape
  (§ 3.3).
- ~~AP4 fallback~~ — **load as-is** without market values (§ 3.4).
- ~~Decision 11 (PMT and Rail & OV)~~ — **load them** (2026-11-10): they are
  in the new sheet with checked tabs. Remove them from `excluded_sources`.

## 4. Code changes required (`manual/`) — implemented 2026-11-10

**Status: implemented** on branch `issue-17-data-refresh` (2026-11-10).
`_process_pension_funds` in `manual/main.py` was rewritten against the
contract below; the metadata map is the module-level `PENSION_FUND_TABS`,
the per-tab rules live in `_read_pension_fund_tab`, and the parsing helpers
are `_parse_number`, `_parse_report_date` and `_canonical_multiplier`. The
dry run (§ 4.5) passes on the 2026-11-10 download — every USD total is within
±4 % of § 6c. Deviations from the text below, all deliberate:

- **Exact-duplicate drop applies to every tab**, not just Vervoer, and the
  2026-11-10 sheet has duplicates in five tabs: AMF 6, LACERA 9, PME 2,
  Rail & OV 1, Vervoer 5 (the § 2 table only knew about Vervoer's). Rows in
  per tab are therefore 338 / 9,695 / 1,361 / 1,053 / 1,270 before the
  merge; the other tabs match § 6c exactly. Every drop is logged per tab.
- **LACERA's 10 blank-issuer rows are all dropped.** Six of them carry a
  name fragment in the ISIN column (`THRASIO`, `RESIDENTIAL`, …); the ISIN
  cleaning (§ 4.2.4) runs first and blanks those, so the "blank issuer *and*
  no ISIN" rule then catches all ten, as § 6c assumes (9,704).
- **Multiplier on rows without a market value is stored as `x1`** (AMF, AP4,
  KPA, and AP3's 139 private-equity rows), matching the prior load's
  convention; their currency and USD columns stay null.
- **USD = round(amount × multiplier × rate)** in one step. The old code
  truncated `int(amount × rate)` *before* applying the multiplier, which
  turned AP3's `29 × 1,000 SEK` into $2,000 instead of $2,953. Totals move
  by less than 0.01 %.
- **Issuer country names/codes are filled both ways**: tabs with a country
  *name* (PensionDanmark, PME) get the ISO code from the map; tabs with a
  *code* (AP2, AP4) get the name. `KOREA` (PME) and `MALTA` (AP2) were added
  to the map. Unmapped names are logged as a warning. The Dutch country-name
  map and the old issuer-string exclusions were removed — the dry run shows
  neither hits (PensionDanmark's `United states` is fixed by uppercasing).
- **Issuer names are whitespace-normalised** (strip, collapse runs) before
  uppercasing; Vervoer's issuer cells have trailing spaces.
- **A blank `Data Source URL` fails the tab** rather than producing a null
  `url` (none are blank today).
- `--pension-file` is **required** whenever the pension funds are processed
  (so also in a no-flag full run), the same way `--nbim-report-date` is for
  NBIM; there is no default filename any more.
- Sheet quirks found during the dry run that § 3 does not list: 69 Vervoer
  rows have a blank `Shareholder - Name` (harmless — `investor_name` comes
  from the map, not the sheet); AMF lists `AstraZeneca`/`Astrazeneca` and
  ~14 dual-listed issuers under both `Foreign Stock` and `Swedish Stock`, so
  the merge collapses AMF to 323 rows. Also 36 bpfBOUW, 15 Rail & OV, 3 AP7
  and 1 PensionDanmark rows have a market value of 0, and a handful of
  LACERA/PKA/AP7 rows are worth under $0.50; the merge nulls all of these
  (its zero → null rule), which is where the per-source `null_usd` counts in
  the validator come from.

The contract as specified (kept for reference; the code follows it except
where noted above):

The old `_process_pension_funds` could not read the new sheet at all: every
tab-name key missed (so `source`/URL/abbreviation were NaN for all rows) and it
subset to columns that no longer exist (`BB Ticker`, `Private Equity -
Vintage Year`) → `KeyError` on the first tab. It was rewritten against this
contract.

### 4.1 Fund metadata map (replaces the four tab-name dicts)

Key on the new tab names. **Keep the existing prod `source` strings** for funds
already in prod so each load is a clean per-source replace and investor pages
keep their identity; new funds get new strings. `investor_name` comes from this
map (the About-page spelling, **uppercased on load** so it matches every other
investor name in the table), **not** from the sheet's `Shareholder - Name`,
which varies (`KPA Pension Pension`, `Tredje AP - Fonden`, `bpfBOUW`) and is a
merge group-by key. URL comes from the per-row `Data Source URL` column.

| Tab | `source` (prod string) | `investor_abbreviation` | `investor_name` | Country | Value multiplier override |
|---|---|---|---|---|---|
| `AMF (checked)` | `AMF PENSIONSFÖRSÄKRING AB` | `AMF` | AMF Pension | SE | — (no values) |
| `AP2 (checked)` | `ANDRA AP-FONDEN` | `AP2` | Andra AP-Fonden | SE | from sheet (`x1_000`) |
| `AP3 (checked)` | `TREDJE AP-FONDEN` | `AP3` | Tredje AP-fonden | SE | from sheet (`x1_000`) |
| `AP4 (checked)` | `FJÄRDE AP-FONDEN` | `AP4` | Fjärde AP-fonden | SE | — (no values, pending § 3.4) |
| `AP7 (checked)` | `SJUNDE AP-FONDEN` | `AP7` | Sjunde AP-fonden | SE | `x1` (sheet currency is now SEK; still assert it) |
| `BPFBOUW (checked)` | `BOUWNIJVERHEID` | `bpfBOUW` | bpfBOUW | NL | from sheet (`x1_00` → treat as `x100`) |
| `DANICA (checked)` | `DANICA PENSION LIVSFORSIKRINGS AB` | (blank) | Danica Pension | DK | from sheet (`x1_000_000`) |
| `KPA (checked)` | `KPA PENSIONSFORSAKRING` | `KPA` | KPA Pension | SE | — (no values) |
| `LACERA (checked)` | `LOS ANGELES COUNTY EMPLOYEES RETIREMENT ASSOCIATION` | `LACERA` | Los Angeles County Employees Retirement Association | US (region California, `US-CA`) | `x1`; default currency `USD` |
| `PENSION DANMARK (checked)` | `PENSIONDANMARK PENSIONSFORSIKRING A/S` | (blank) | PensionDanmark | DK | from sheet (`x1_000_000`) |
| `PKA (checked)` | `PENSIONSKASSERNES ADMINISTRATION A/S` | `PKA` | Pensionskassernes Administration | DK | `x1` |
| `PME (checked)` | `PENSIOENFONDS VAN DE METALEKTRO` | `PME` | PME pensioenfonds | NL | `x1` |
| `PMT (checked)` | `PENSIOENFONDS METAAL EN TECHNIEK` (new) | `PMT` | Metal and Technology Pension Fund | NL | `x1` |
| `RAILOV (checked)` | `PENSIOENFONDS RAIL & OV` (new) | `Rail & OV` | Rail & OV | NL | `x1` |
| `VERVOER (checked)` | `PENSIOENFONDS VERVOER` | (blank) | Pensioenfonds Vervoer | NL | from sheet (`x1_000`) |

(Sampension — `SAMPENSION ADMINISTRATIONSSELSKAB A/S` / blank / Sampension / DK
/ `x1` — has no tab today; keep its row in the map so the re-scraped tab loads
without a code change.)

Note the AP2 consolidation retires the stray `P2` abbreviation. `investor_type`
stays `PENSION FUND`; `investor_region_*` blank except LACERA.

### 4.2 Parsing rules

1. Read every tab except `SOURCES`; strip header whitespace; apply a
   canonical-rename map (`Security - Market Value` → `… - Amount`, `Report Date
   URL` → `Data Source URL`, AP4 `Issuer - Country Name` → `Issuer - Country
   Code`); add any missing canonical column as empty. Fail loudly on a tab
   name not in the metadata map (new fund = new decision, not silent NaNs).
2. Drop exact duplicate rows per tab (Vervoer). Drop rows whose issuer name is
   blank *and* has no ISIN. Drop rows whose issuer is a bare country name
   (bpfBOUW subtotals) — maintain a small explicit list.
3. Numbers: remove all whitespace, then handle `,` as thousands separator
   unless the string also has a `.`-less comma-decimal pattern; strip `%` and
   convert comma decimals for PKA. Parse dates with `dayfirst=True` fallback
   for `dd-mm-yyyy` strings (Danica).
4. ISIN: truncate to 12 chars (AP3); blank anything not matching
   `^[A-Z]{2}[A-Z0-9]{9}[0-9]$` (LACERA fragments) — and **log the count per
   tab** so the re-scraped Sampension/AP4 tabs can be checked when they return.
5. Multiplier: sheet value if present, else the § 4.1 override, else `x1`.
   Normalise the string first (strip, lower, remove underscores: `x1_00` →
   `x100`, `x1_000` → `x1000`) and map `x1`/`x100`/`x1000`/`x1000000`; fail
   loudly on anything else. Store the canonical `x1`/`x100`/`x1_000`/
   `x1_000_000` spelling in `security_market_value_multiplier`.
6. Currency: sheet value, else the § 4.1 default (LACERA → USD). Assert AP7 is
   all `SEK` (it is now; a regression would silently inflate it ~10×).
7. `security_type`: AMF `Private Swedish Stock` → `PRIVATE EQUITY`; AP3 rows
   with no ISIN and no value → `PRIVATE EQUITY FUND`; LACERA `EQUITY` and
   everything else → `STOCKS` (prod's label). Drop the old `CORPORATE BOND`
   filter and `FUND EQ` rule only if nothing in the sheet uses them (nothing
   does today).
8. `stock_percent_ownership` / `stock_percent_voting_power`: map for **AP4
   only**. Do not map for PKA (§ 3.5 — weight). AP7's column no longer exists.
9. Remove `excluded_sources` entirely (decision 11 confirmed; Detailhandel has
   no tab). Remove the old issuer-string exclusions and Dutch country-name map
   unless the dry run shows they still hit.

### 4.3 Currency map

**Done 2026-11-10**: `data/input/currency_country_map.json` exists with the
content below and `.gitignore` negates it (`!data/input/`, `data/input/*`,
`!data/input/currency_country_map.json`), so it is committed with the code;
`git check-ignore data/input/currency_country_map.json` exits 1.

Rebuild `data/input/currency_country_map.json`. Format is `{currency code: IMF
area code}`; IMF area codes are ISO-3166 alpha-3 (`SWE`, `DNK`, `USA`, `NOR`)
except the euro area, which is `G163`. With AP7 forced to SEK the workbook
needs only:

```json
{"SEK": "SWE", "DKK": "DNK", "EUR": "G163", "USD": "USA", "NOK": "NOR"}
```

If AP7 is ever loaded in its 36 trading currencies instead, extend the map
accordingly. Add a `.gitignore` negation so the file is committed — it is tiny
and losing it again costs a day.

IMF coverage checked 2026-09-09: annual 2025 rates exist for SEK/DKK/EUR
(0.1018 / 0.1510 / 1.1300 USD per unit); 2026 has monthly rates through
August, so the 2026-dated tabs (PKA, PME, PMT, KPA) convert at a
partial-year average that will drift slightly if re-run later. Fine, but note
it in the release notes.

### 4.4 CLI

**Done 2026-11-10**: `--pension-only` is in the `mode` group and
`--pension-file PATH` is required whenever the pension funds are processed
(`main.py` errors out otherwise). Run from `manual/`:

```bash
python main.py --pension-only --pension-file ../data/input/pension_funds_2026-11-10.xlsx
```

Add `--pension-only` (skip SEC and NBIM, feed empty frames to the merge — same
pattern as `--sec-only`) and `--pension-file <path>` instead of the hardcoded
filename. Reject `--pension-only` together with `--sec-only`/`--nbim-only`.

Since 2026-11-10 (§ 5b) `main()` already has the scaffolding for this:
`--sec-only` / `--nbim-only` live in an argparse mutually-exclusive group
named `mode` (so the rejection is free), and the flags are reduced to a
`sources` set that gates each `_process_*` call. Adding `--pension-only` is
one `mode.add_argument(...)` plus one `elif args.pension_only: sources =
{"pension"}`; the empty-frame substitution for skipped sources is already
generic. Check that `_process_pension_funds` alone returns every column
`_merge_datasets` aggregates (the NBIM branch does; the SEC branch needs
`security_vintage_year` / `stock_percent_ownership` patched in, which
`main()` does only when `sources == {"sec"}`).

### 4.5 Dry run (mandatory before prod)

Run against the downloaded `.xlsx` and check, per fund, against § 6c: rows in
vs rows out (minus documented drops), USD total within ~15 % of the target, no
null `source`/`url`/`investor_name`, null-ISIN and null-USD counts as expected,
one `investor_name` per source, `document_report_date` matching the tab.
`python manual/validate_release.py data/output/shareholder_tracker_release_YYYYMMDD.csv --targets manual/validation_targets_2026-11.csv`
prints these per source and flags the checks (exits non-zero on any WARN).

**Dry run of 2026-11-10** (`pension_funds_2026-11-10.xlsx`, IMF rates fetched
that day: SEK 0.10183, DKK 0.15102 (2025) / 0.15488 (2026 partial), EUR
1.12998 (2025) / 1.16286 (2026 partial)): 27,114 rows, 15 sources, validator
exit 0 with no warnings. Rows are post-merge; the merge collapses duplicate
securities (LACERA 9,695 → 5,725, AMF 338 → 323).

| Source | Rows out | USD bn | § 6c target | Diff | Flag |
|---|---|---|---|---|---|
| AMF | 323 | — | — | | n/a |
| AP2 | 1,288 | 19.4 | 19.4 | −0.1 % | PASS |
| AP3 | 1,076 | 27.9 | 27.9 | −0.1 % | PASS |
| AP4 | 1,306 | — | — | | n/a |
| AP7 | 1,913 | 134.4 | 134.4 | +0.0 % | PASS |
| bpfBOUW | 4,225 | 15.5 | 16.2 | −4.0 % | PASS |
| Danica | 2,390 | 34.3 | 34.3 | −0.0 % | PASS |
| KPA | 552 | — | — | | n/a |
| LACERA | 5,725 | 29.5 | 29.5 | −0.2 % | PASS |
| PensionDanmark | 1,591 | 20.5 | 20.5 | +0.2 % | PASS |
| PKA | 1,660 | 12.7 | 12.4 | +2.3 % | PASS |
| PME | 1,360 | 18.7 | 18.2 | +2.9 % | PASS |
| PMT | 1,384 | 23.2 | 22.6 | +2.7 % | PASS |
| Rail & OV | 1,052 | 8.8 | 8.8 | +0.1 % | PASS |
| Vervoer | 1,269 | 12.4 | 12.4 | −0.3 % | PASS |

Also verified: one `investor_name` per source; no `P2`; no null `source`,
`url` or `investor_name`; one `document_report_date` per source matching
its tab; AP4 ownership on 155 rows (voting on 153); PKA ownership null on
all rows; bpfBOUW multiplier `x100`; Vervoer `x1_000`; LACERA `USD` on all
rows; AP7 `SEK` on all rows; 103 LACERA ISINs blanked, 22 AP3 ISINs
truncated; AMF 16 `PRIVATE EQUITY`, AP3 139 `PRIVATE EQUITY FUND`. The
2026-dated tabs (PKA, PME, PMT) run +2–3 % above § 6c because they convert
at the 2026 partial-year average (§ 4.3), not the 2025 annual rate.

## 5. NBIM (Norges Bank) refresh

Self-contained: no workbook, no currency conversion, no Google Sheet. Takes
about 30 minutes once the § 5b code changes are in place.

### 5a. What we load, and where it comes from

- **Source page:** <https://www.nbim.no/en/investments/all-investments/>. It is a
  JavaScript app over `https://www.nbim.no/api/investments/v2/`. Its
  **Download** button offers four things, each scoped to the asset class and
  date currently selected on the page:
  - *your selection* (xlsx / csv) — built in the browser from the visible
    table, so it reflects whatever filters are on. **This is what the
    December 2025 load used** (headers `company, value (USD), sector,
    ownership, country`). Don't use it again — it is not reproducible and
    lacks the NOK and voting columns.
  - *total holdings by country* (xlsx / csv) — served by a stable endpoint.
    **Use this one.**
- **Asset class: Equity only.** nbim.no also publishes Fixed income (bonds by
  issuer), Real estate (property partnerships), and Renewable energy
  infrastructure (project stakes). Real estate and renewables are not
  securities and don't fit the `investment` schema. Fixed income could be
  modeled as a second `security_type` later; it is not loaded today and this
  runbook doesn't cover it.
- **Report endpoint** (the *total holdings by country* download):

  ```text
  https://www.nbim.no/api/investments/v2/report/?assetType=eq&date=<YYYY-MM-DD>&fileType=csv
  ```

  `assetType` is `eq` / `fi` / `re` / `ri`. `date` must be one of the published
  snapshot dates exactly (a bare year 404s).
- **Snapshot dates:** every 31 December back to 1998, plus half-year
  (30 June) snapshots from 2024 on. Annual holdings are published with the
  annual report (Feb/Mar); H1 holdings with the half-year report (mid August).
  The authoritative list is in
  `https://www.nbim.no/api/investments/v2/init.json` → `data.details`
  (`label`, `date`, `interim`).
- **File format:** UTF-16 with BOM, **semicolon**-delimited, one header row.
  Columns:

  | Column | Maps to |
  |---|---|
  | `Region` | (not loaded) |
  | `Country` | `issuer_country_name` (→ code via the existing map) |
  | `Name` | `issuer_name` |
  | `Industry` | `issuer_sector` |
  | `Market Value(NOK)` | (not loaded — USD is native in the file) |
  | `Market Value(USD)` | `security_market_value_amount` and `…_amount_usd` |
  | `Voting` | `stock_percent_voting_power` (string like `1.43%`) |
  | `Ownership` | `stock_percent_ownership` (string like `1.43%`) |
  | `Incorporation Country` | (not loaded; mostly blank) |

  One row per company; no ISIN, ticker, or share count. Values are whole USD
  (`x1` multiplier, conversion rate 1).
- **Reference numbers** (Equity, from the endpoint):

  | Snapshot | Rows | Total USD |
  |---|---|---|
  | 2025-06-30 (what prod has today) | 8,374 | $1,387.9 bn |
  | 2025-12-31 | 7,201 | $1,505.2 bn |
  | 2026-06-30 | 7,077 | $1,660.9 bn |

  Row counts falling while value rises is expected (NBIM has been trimming
  small-cap positions). A sanity target for any date is the `nav` entry in
  `init.json` with `a == "eq"` and matching `d`: `v.e` is the USD total and
  `v.n` the NOK total.

### 5b. Code changes required (one-time — implemented 2026-11-10)

`_process_nbim_investments` in `manual/main.py` now reads the endpoint file.
What was done, against the original list (all items done unless noted):

1. ~~Read with `pd.read_csv(path, sep=";", encoding="utf-16")`.~~ Done. The
   function raises `ValueError` if any of the six mapped § 5a columns is
   missing from the header, so a wrong download (e.g. the browser export, or
   an HTML 404 body) fails before anything is written.
2. ~~Replace the column map with the § 5a mapping; strip `%`, cast to float;
   add `stock_percent_ownership` and `stock_percent_voting_power` to the
   final column list.~~ Done. **Deviation:** nbim.no prints holdings below
   0.005% as `0%`. `_merge_datasets` nulls zeroes in every numeric column for
   every source (unchanged — out of scope), so those rows land as `NULL`
   rather than `0`. For 2026-06-30 that is 143 rows for ownership and 205 for
   voting; the other 6,934 / 6,872 are populated. The function also returns
   every column the merge expects (`security_principal_amount*`,
   `stock_number_of_shares`, `stock_voting_auth_*` as empty / NaN), so it can
   be merged on its own without `main()` patching columns in.
3. ~~Stop hardcoding the date; add `--nbim-report-date`.~~ Done. The flag is
   validated as strict `YYYY-MM-DD` (`2026-6-30` is rejected) and is
   **required whenever NBIM is processed** — that includes the no-flag
   "all sources" mode, which previously needed no arguments.
4. ~~Add `--nbim-only`.~~ Done. `--sec-only` and `--nbim-only` are an argparse
   mutually-exclusive group; `main()` turns the flags into a `sources` set
   (`{"sec", "nbim", "pension"}` narrowed to one) and substitutes an empty
   copy of the processed frame for each skipped source. `--pension-only`
   (§ 4.4) slots in as one more flag in that group plus one `elif`.
5. ~~Keep the existing constants.~~ Done, unchanged.
6. ~~Check `issuer_country_code` coverage.~~ Done: the 2026-06-30 file needed
   `BANGLADESH`, `JORDAN`, `KENYA`, `MOROCCO` and `TÜRKIYE` (nbim.no spells it
   with the diaeresis; `TURKEY` is kept too). The misspelt `BAMAHAS` key was
   corrected to `BAHAMAS`. Any name still unmapped is logged as a `WARNING`
   with the offending names rather than failing the run — check the log, or
   the null-count in § 5c step 5.
7. ~~Remove the dead `"NBIM"` special case in the SEC branch.~~ Done; SEC
   `investor_abbreviation` is now always `""`, as it was in practice.

Acceptance run on `data/input/nbim_equity_2026-06-30.csv`: 7,077 rows, all
`NORGES BANK` / `2026-06-30`, USD sum $1,660.891 bn (matches § 5a), zero null
`issuer_country_code`, URL and `text` populated on every row, 37 columns in
`\copy` order. `--sec-only` was exercised on a 50k-row sample of the SEC
export (full file is 750 MB): single SEC source, empty abbreviations.

### 5c. Refresh steps

Prereqs per [REFRESH.md](REFRESH.md) § 2: proxy running, `PGHOST=127.0.0.1`,
password from Secret Manager. Run this separately from the SEC and workbook
loads so each verifies in isolation.

1. **Pick the snapshot.** List what nbim.no has published:

   ```bash
   curl -s "https://www.nbim.no/api/investments/v2/init.json" | python3 -c "import sys,json; [print(d['label'], d['date'][:10]) for d in json.load(sys.stdin)['data']['details'][:4]]"
   ```

   Use the newest date. Set it once for the rest of the steps:

   ```bash
   export NBIM_DATE=2026-06-30
   ```

2. **Download the Equity report** into `data/input/`:

   ```bash
   curl -fL -A "Mozilla/5.0" -o "data/input/nbim_equity_${NBIM_DATE}.csv" "https://www.nbim.no/api/investments/v2/report/?assetType=eq&date=${NBIM_DATE}&fileType=csv"
   ```

   A 404 (HTML body) means the date isn't a published snapshot — recheck step 1.

3. **Sanity-check the file** — row count and USD total should match the
   `init.json` `nav` figure for `eq` on that date to within rounding:

   ```bash
   python3 -c "import pandas as pd,os; df=pd.read_csv(f\"data/input/nbim_equity_{os.environ['NBIM_DATE']}.csv\", sep=';', encoding='utf-16'); print(len(df), 'rows'); print(round(df['Market Value(USD)'].sum()/1e9,1), 'bn USD'); print(df['Country'].nunique(), 'countries'); print(df.columns.tolist())"
   ```

4. **Verify + back up prod** (REFRESH.md § 3). Record the current `NORGES BANK`
   count and report date so the load can be checked against them:

   ```sql
   SELECT COUNT(*), MIN(document_report_date), MAX(document_report_date), MIN(last_accessed_date)
   FROM investment WHERE source = 'NORGES BANK';
   ```

5. **Transform:**

   ```bash
   cd manual && python main.py --nbim-only --nbim-report-date "$NBIM_DATE" && cd ..
   ```

   → `data/output/shareholder_tracker_release_YYYYMMDD.csv` containing only
   `NORGES BANK` rows. Check before loading: row count equals the input file's
   (one row per company, so the merge's group-by should not collapse
   anything), `document_report_date` is `$NBIM_DATE` on every row, USD sum
   matches step 3, no null `issuer_country_code`, and `stock_percent_ownership`
   is populated except on rows the file reports as `0%` (§ 5b item 2; 143 rows
   for 2026-06-30). A `WARNING` line naming unmapped countries means the map in
   `_process_nbim_investments` needs those names before loading. `python manual/validate_release.py <that csv> --targets manual/validation_targets_2026-11.csv`
   prints all of these per source.

6. **Load in one transaction** — replace the single source:

   ```sql
   BEGIN;
   DELETE FROM investment WHERE source = 'NORGES BANK';
   \copy investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date) FROM 'data/output/shareholder_tracker_release_YYYYMMDD.csv' WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL');
   COMMIT;
   ```

7. **Verify:**

   ```sql
   SELECT COUNT(*), MIN(document_report_date), MAX(document_report_date),
          ROUND(SUM(security_market_value_amount_usd) / 1e9, 1) AS usd_bn,
          COUNT(*) FILTER (WHERE stock_percent_ownership IS NULL) AS null_ownership,
          COUNT(*) FILTER (WHERE issuer_country_code IS NULL) AS null_country_code
   FROM investment WHERE source = 'NORGES BANK';
   -- Everything else must be untouched:
   SELECT source, COUNT(*) FROM investment GROUP BY source ORDER BY 2 DESC;
   ```

   The website reads live, so the new rows show immediately. Spot-check the
   Norges Bank investor page for a large holding (e.g. NVIDIA, Microsoft).

8. **Downloads page (optional):** regenerate the combined release from prod with
   `python manual/export_release.py` and publish per REFRESH.md § 2g.

## 6. Workbook refresh

Prereqs per [REFRESH.md](REFRESH.md) § 2: proxy running, `PGHOST=127.0.0.1`,
password from Secret Manager. Run this *separately* from the SEC and NBIM
loads so each verifies in isolation.

### 6a. Per-fund decisions from the data team (2026-09-09)

The workbook is not a full replacement of the pension rows in prod. Apply these
fund by fund; the load steps refer back to this table.

**Keep existing prod rows untouched — no update in the sheet:**

| Fund | `source` string in prod | Rows | Report date in prod | Why |
|---|---|---|---|---|
| BPL Pensioen | `STICHTING BPL PENSIOEN` | 4,672 | 2023-12-31 | no newer disclosure |
| PFZW | `PENSIOENFONDS ZORG EN WELZIJN` | 5,428 | 2024-12-31 | no update in the sheet |
| Stichting Pensioenfonds ABP | `STICHTING PENSIOENFONDS ABP` | 2,019 | 2025-06-30 | no update in the sheet |
| Sampension | `SAMPENSION ADMINISTRATIONSSELSKAB A/S` | 1,181 | 2025-08-31 | new tab was mis-scraped and deleted 2026-11-10; re-scrape pending (§ 3.3) |

These four have no tab in the workbook. **Never include their source strings
in the load's DELETE**, and confirm in the post-load verification that their
counts are exactly unchanged. Their `last_accessed_date` stays 2025-12-18.

**Parked, not partner-requested (decision 2026-11-10):** BPL's 1,148 populated
`stock_percent_ownership` values look like portfolio weights (§ 3.5), which the
website renders as an ownership sentence. The partner never raised BPL and has
disputed the same reading for PKA, so **leave the values as-is** until they
confirm. Raise it together with the open PKA question. If they agree, the fix
is one statement, reversible from the backup table:

```sql
UPDATE investment SET stock_percent_ownership = NULL
 WHERE source = 'STICHTING BPL PENSIOEN' AND stock_percent_ownership IS NOT NULL;
-- expect UPDATE 1148
```
(The `SOURCES` tab lists ZORG&WELZJIN with a 2025-12-31 file date even though
there is no PFZW tab — the instruction is to keep the existing rows
regardless.)

**Replace — funds with a tab and rows in prod today:**

AMF, AP2 (both `AP2` and `P2` abbreviation rows), AP3, AP4, AP7, bpfBOUW,
Danica, KPA, PensionDanmark, PKA, PME, Vervoer. Their prod `source` strings are
in § 4.1; the DELETE lists exactly those 12 strings. AP4 is replaced with rows
that have **no market values** (§ 3.4) — expected and accepted.

**New — first appearance in prod:**

| Fund | Tab | Rows | Report date | Notes |
|---|---|---|---|---|
| Los Angeles County Employees Retirement Association (LACERA) | `LACERA (checked)` | 9,714 | 2025-09-30 | First US pension in the Tracker. Does **not** file a 13F (data team, and confirmed: no LACERA rows in the 2026-06-30 SEC quarter — the only `LOS ANGELES` filer is `LOS ANGELES CAPITAL MANAGEMENT LLC`, unrelated). All `EQUITY`, USD. Sheet issues § 3.7. |
| Pensioenfonds Metaal en Techniek (PMT) | `PMT (checked)` | 1,384 | 2026-03-31 | Pending decision 11. |
| Pensioenfonds Rail & OV | `RAILOV (checked)` | 1,054 | 2025-03-31 | Pending decision 11. |

**Excluded — not loaded, no rows in prod:**

| Fund | Reason |
|---|---|
| Pensioenfonds Detailhandel | The published disclosure mixes equity and fixed-income holdings with no way to separate them. The data team removed the tab (as they did in the previous round). Never in prod; stays out. Its `SOURCES` entry (2026-03-31) is stale — ignore. |

**Relabel as pension funds — SEC side, not the workbook:**

Two Dutch pension asset managers file 13Fs and are currently tagged
`INSTITUTIONAL INVESTOR`. The data team wants them shown as pension funds (the
website's "Pension Funds" filter is `investor_type ILIKE 'Pension Fund'`).

| 13F filer (`investor_name` in prod) | CIK | Rows (2026-06-30 qtr) | Action |
|---|---|---|---|
| `PGGM INVESTMENTS` | 0001472190 | 59 | → `PENSION FUND` |
| `APG ASSET MANAGEMENT N.V.` | 0001434819 | 493 | → `PENSION FUND` |
| `APG ASSET MANAGEMENT US INC.` | 0001323255 | 61 | → `PENSION FUND` (confirmed 2026-11-10) |

How the label works: `_process_sec_investments` in `manual/main.py` sets
`investor_type = 'PENSION FUND'` for any SEC filer whose name appears in
`data/input/sec_pension_funds.csv`, else `INSTITUTIONAL INVESTOR`. That file
is gitignored and is regenerated *from prod* (REFRESH.md § 2b), so prod is the
durable record. The `text` search column does not include `investor_type`, so
an in-place UPDATE is complete on its own.

Steps (can run any time, independent of the other loads):

1. Fix prod directly, in one transaction (proxy + `PGHOST=127.0.0.1` per
   REFRESH.md § 2):

   ```sql
   BEGIN;
   UPDATE investment
      SET investor_type = 'PENSION FUND'
    WHERE source = 'U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)'
      AND investor_name IN ('PGGM INVESTMENTS', 'APG ASSET MANAGEMENT N.V.',
                            'APG ASSET MANAGEMENT US INC.');
   -- expect UPDATE 613 on the 2026-06-30 quarter (59 + 493 + 61)
   COMMIT;

   SELECT investor_name, investor_type, COUNT(*)
     FROM investment
    WHERE investor_name LIKE 'PGGM%' OR investor_name LIKE 'APG %'
    GROUP BY 1, 2 ORDER BY 1;
   ```

   The website reflects it immediately.
2. Make it survive the next SEC refresh: the label file is read at transform
   time, so a stale local copy would silently revert the change. Either
   regenerate `data/input/sec_pension_funds.csv` from prod *after* step 1
   (REFRESH.md § 2b), or append the three names by hand:

   ```bash
   printf '%s\n' 'PGGM INVESTMENTS' 'APG ASSET MANAGEMENT N.V.' 'APG ASSET MANAGEMENT US INC.' >> data/input/sec_pension_funds.csv
   ```

   Then check REFRESH.md § 2f's pension-label verification after the next SEC
   load.
3. The Downloads-page release only picks the new label up when the combined
   release is next regenerated with `manual/export_release.py`.

### 6b. About-page text (implemented in branch `issue-17-data-refresh`; ships with the pipeline merge, after the loads)

`web/app/about/page.tsx` has a bulleted list of data sources. The second
bullet (previously "The shareholdings of 17 European pension funds …") has
been replaced in branch `issue-17-data-refresh` (2026-11-10) with this text,
supplied by the data team (2026-09-09), verbatim, with the LACERA sentence
appended as the bullet's last sentence:

> The shareholdings of 19 European pension funds that do not report to the
> U.S. SEC. This database compiles information disclosed by the pension funds
> on their websites. The pension funds are: Norges Bank Investment Management,
> Pensioenfonds Vervoer, Sampension, Rail & OV, Metal and Technology Pension
> Fund, PME pensioenfonds, Pensionskassernes Administration, PensionDanmark,
> KPA Pension, Danica Pension, bpfBOUW, Sjunde AP-fonden, Fjärde AP – Fonden,
> Tredje AP – Fonden, Andra AP-Fonden, AMF Pension, BPL Pensioen, PFZW, and
> Stichting Pensioenfonds ABP.
>
> We have also included one U.S. pension fund that does not disclose to the
> U.S. SEC: Los Angeles County Employees Retirement Association.

Notes:

- The 19 = the 16 workbook funds minus LACERA, plus the three "keep" funds
  and NBIM. Rail & OV and PMT are new to the list, so publishing this text
  presumes decision 11 lands as "load them".
- PGGM and APG (relabel above) are 13F filers and belong to the first bullet,
  not this one.
- The first bullet's "more than 4,200 institutional investors" figure is
  independent of this work; refresh it from prod if convenient:
  `SELECT COUNT(DISTINCT investor_name) FROM investment WHERE source LIKE 'U.S.%';`
- This is a code change deployed via Vercel, unlike the data loads, which show
  immediately. It is already in branch `issue-17-data-refresh` alongside the
  pipeline code, so it ships in the same merge. Merge only after the NBIM
  (§ 5c) and workbook (§ 6d) loads are live in prod, not before — otherwise
  the page names funds that are not loaded yet.

### 6c. Dry-run and post-load targets

Native totals from the 2026-09-09 sheet under the § 4.1 multipliers; USD at
2025 IMF annual averages (SEK 0.1018, DKK 0.1510, EUR 1.130). Prod column is
the 2025-12-18 load, for scale. A result outside roughly ±15 % of the target
means a unit or currency problem, not market movement.

| Fund | Rows in (after drops) | Native total | ≈ USD bn | Prod USD bn |
|---|---|---|---|---|
| AMF | 344 | — | — | — |
| AP2 | 1,289 | 190.2 bn SEK | 19.4 | 16.7 |
| AP3 | 1,078 (139 PE rows have no value) | 273.6 bn SEK | 27.9 | 26.7 |
| AP4 | 1,306 | — (no values, § 3.4) | — | 24.7 → 0 |
| AP7 | 1,919 | 1,320.4 bn SEK | 134.4 | 127.7 |
| bpfBOUW | 4,225 (3 subtotal rows dropped) | 14.3 bn EUR (`x1_00` = ×100) | 16.2 | 19.1 |
| Danica | 2,392 | 227.1 bn DKK | 34.3 | 31.1 |
| KPA | 552 | — | — | — |
| LACERA | 9,704 (10 blank issuers) | 29.5 bn USD | 29.5 | new |
| PensionDanmark | 1,593 | 18.2 bn EUR | 20.5 | 18.4 |
| PKA | 1,660 | 81.9 bn DKK | 12.4 | 8.9 |
| PME | 1,363 | 16.1 bn EUR | 18.2 | 16.7 |
| PMT | 1,384 | 20.0 bn EUR | 22.6 | new |
| Rail & OV | 1,054 | 7.8 bn EUR | 8.8 | new |
| Vervoer | 1,270 (5 dupes dropped) | 10.9 bn EUR (`x1_000`) | 12.4 | 12.5 |

Sampension is not loaded (kept on prod rows). Totals re-checked on the
2026-11-10 download: unchanged except that the AP7/bpfBOUW/Vervoer figures now
follow from the sheet's own currency and multiplier columns rather than from
code overrides.

Rows *out* will be lower where the merge collapses duplicate securities
(LACERA holds the same ISIN in several accounts). The code also drops exact
duplicate rows in every tab, so "rows in" is lower than the table for AMF
(338), LACERA (9,695), PME (1,361) and Rail & OV (1,053) as well — see § 4.
Measured results of the 2026-11-10 dry run are in § 4.5.

### 6d. Refresh steps (§ 3 blockers answered and § 4 implemented, 2026-11-10)

1. **Download the sheet as `.xlsx`** into `data/input/` (§ 2 link).
2. **Verify + back up** (REFRESH.md § 3): run the `GROUP BY source` breakdown,
   confirm the 17 current strings and counts, create and count a dated backup
   table.
3. **Transform:**

   ```bash
   cd manual && python main.py --pension-only --pension-file "../data/input/<workbook>.xlsx" && cd ..
   ```

   → `data/output/shareholder_tracker_release_YYYYMMDD.csv` (workbook rows
   only).
4. **Validate locally against § 6c** before touching prod. Also: exactly one
   `investor_name` per `source`; no `P2` abbreviation; no rows with a null
   `url`; per-tab counts of blanked ISINs match § 3 expectations.
5. **Load in one transaction.** The DELETE lists the 12 "replace" sources from
   § 6a (PMT/Rail & OV/LACERA have no prod rows to delete). It must **not**
   list `NORGES BANK` or the four "keep" funds:

   ```sql
   BEGIN;
   DELETE FROM investment WHERE source IN (
     'AMF PENSIONSFÖRSÄKRING AB', 'ANDRA AP-FONDEN', 'TREDJE AP-FONDEN',
     'FJÄRDE AP-FONDEN', 'SJUNDE AP-FONDEN', 'BOUWNIJVERHEID',
     'DANICA PENSION LIVSFORSIKRINGS AB', 'KPA PENSIONSFORSAKRING',
     'PENSIONDANMARK PENSIONSFORSIKRING A/S', 'PENSIONSKASSERNES ADMINISTRATION A/S',
     'PENSIOENFONDS VAN DE METALEKTRO', 'PENSIOENFONDS VERVOER');
   -- expect DELETE 18,674 = 40,348 total − 8,374 NBIM − 13,300 kept (BPL 4,672 + PFZW 5,428 + ABP 2,019 + Sampension 1,181)
   \copy investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date) FROM 'data/output/shareholder_tracker_release_YYYYMMDD.csv' WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL');
   COMMIT;
   ```

6. **Verify**: rerun the `GROUP BY source` breakdown — SEC count unchanged;
   `NORGES BANK` unchanged; the four "keep" funds unchanged (4,672 / 5,428 /
   2,019 / 1,181); the 12 replaced sources present with § 6c counts; the new
   sources present; `FJÄRDE AP-FONDEN` has null USD on every row (expected).
   The website reflects the change immediately.
7. **Regenerate the combined release** for the Downloads page from prod with
   `python manual/export_release.py` (REFRESH.md § 2g).
8. **Merge the branch** — the About-page text (§ 6b) is already in
   `issue-17-data-refresh`; merge after the loads, not before.

## 7. Known caveats

- **Mixed vintages by design**: pension report dates (2023-12 → 2026-05) sit
  alongside quarter-pinned SEC data. Each row carries `document_report_date`,
  so it's visible, but it's an editorial choice the team owns.
- **No cross-source dedup exists** (see § 1). There is no NBIM/SEC or
  LACERA/SEC overlap in the current data. If dedup is ever wanted, it's new
  logic, not a regression fix.
- **Percentage columns were `numeric(6,5)`** (max 9.99999) until the November
  2026 refresh widened them to `numeric(8,5)` (§ 8.3). Any future source with
  a stake above 10 % needs that schema, and `export_release.py`'s precision
  note in REFRESH.md § 2g still describes 5-decimal rounding, which is
  unchanged.
- **NBIM rows have no identifiers** (no ISIN/CUSIP/ticker/share count) and are
  one row per company, aggregated across share classes by nbim.no. Search and
  matching for them is by issuer name only.
- **Percent-ownership semantics differ by fund.** AP2/AP3/AP4 (and NBIM, once
  the § 5 load runs) report real ownership stakes; PKA, AP7, BPL and Danica reported
  portfolio weights, which the website renders as an ownership sentence.
  After this refresh the sentence appears only for AP2, AP3, AP4 and NBIM:
  PKA is not mapped, AP7's column was deleted from the sheet, Danica's new tab
  has no such column. **BPL's values remain in prod** (not partner-requested
  to change, § 6a), so BPL cards keep showing the sentence until the partner
  weighs in. Any fund that later adds a percentage column must be classified
  first (§ 3.5).
- **AP4 has no market values** after this refresh (prod had $24.7 bn). The
  data team accepted this pending a re-scrape; Sampension is likewise frozen
  on 2025-08-31 rows. When either re-scraped tab arrives, re-run § 6c for
  that fund only and reload just that source.
- **Unit conventions are per fund and hand-verified** (§ 4.1). Any new tab or
  changed multiplier must be checked against fund size before loading; § 6c
  is the reference.
- The workbook copy analysed here (2026-09-09) and the earlier one (2026-09-01)
  are session artifacts; re-download a fresh copy for any real run and re-run
  the § 6c totals on it.

## 8. Prod run sheet — November 2026 refresh

Everything in §§ 5–6 collapsed into one ordered checklist, with the numbers
measured on the 2026-11-10 dry runs. Work top to bottom in one sitting if
possible; each numbered block is its own transaction and can be re-run or
rolled back on its own. Nothing here needs a deploy until block 7.

### 8.0 Pre-flight (10 min)

```bash
cd ~/repo/idi-shareholder-tracker && git checkout issue-17-data-refresh && git pull
gcloud auth login && gcloud auth application-default login
gcloud config set project shareholder-tracker
```

Terminal 1 (leave running):

```bash
./cloud-sql-proxy --port 5432 shareholder-tracker:us-central1:idi-shareholder-db-prod
```

Terminal 2 (every psql/python step below runs here; re-export after any new
shell):

```bash
export PGHOST=127.0.0.1 PGPORT=5432 PGUSER=postgres PGDATABASE=postgres
export PGPASSWORD="$(gcloud secrets versions access latest --secret=POSTGRES_PASSWORD)"
psql -c "SELECT 1;"
```

Then open an interactive session — **every SQL block in §§ 8.1–8.5 is pasted
at the `postgres=#` prompt**, and the `\copy` lines are psql meta-commands
that only work there (not via `psql -c`). Start it from the repo root, because
`\copy` reads file paths relative to psql's working directory and the paths
below are written as `data/output/...`:

```bash
cd ~/repo/idi-shareholder-tracker && psql
```

The `python main.py` / validator / `\copy`-export shell steps in §§ 8.2–8.4
run outside psql: use a third terminal tab (re-export the `PG*` variables
there), or `\q` and reopen psql after each one.

Inputs that must exist locally:

| File | How |
|---|---|
| `data/input/nbim_equity_2026-06-30.csv` | present from the dry run; or re-download per § 5c step 2 |
| `data/input/pension_funds_2026-11-10.xlsx` | present from the dry run; **re-download** (§ 2 link, `File → Download → .xlsx`) if the sheet may have changed, then re-run the § 8.3 dry run and compare to § 6c before loading |
| `data/input/currency_country_map.json` | committed |
| `data/input/sec_pension_funds.csv` | regenerated in § 8.2 |

The pipeline writes `data/output/shareholder_tracker_release_<YYYYMMDD>.csv`
regardless of mode, so **rename each output before the next transform** (the
commands below do).

### 8.1 Baseline and backup (5 min)

```sql
SELECT source, COUNT(*) AS rows FROM investment GROUP BY source ORDER BY rows DESC;
```

Expected: 18 rows — SEC 1,932,680; NORGES BANK 8,374; PENSIOENFONDS ZORG EN
WELZIJN 5,428; STICHTING BPL PENSIOEN 4,672; PENSIONSKASSERNES ADMINISTRATION
A/S 2,792; BOUWNIJVERHEID 2,457; DANICA … 2,234; SJUNDE AP-FONDEN 2,073;
STICHTING PENSIOENFONDS ABP 2,019; PENSIOENFONDS VERVOER 1,485; PENSIONDANMARK
… 1,443; PENSIOENFONDS VAN DE METALEKTRO 1,398; FJÄRDE AP-FONDEN 1,368; TREDJE
AP-FONDEN 1,295; ANDRA AP-FONDEN 1,283; SAMPENSION … 1,181; KPA
PENSIONSFORSAKRING 548; AMF PENSIONSFÖRSÄKRING AB 298. Total 1,973,028. If the
SEC count differs, a SEC refresh has happened since — fine, but note the new
number for § 8.6.

```sql
CREATE TABLE investment_backup_20261110 AS SELECT * FROM investment;
SELECT COUNT(*) FROM investment_backup_20261110;   -- must equal the total above
```

### 8.2 SEC-side corrections (2 min, one transaction)

```sql
BEGIN;
UPDATE investment
   SET investor_type = 'PENSION FUND'
 WHERE source = 'U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)'
   AND investor_name IN ('PGGM INVESTMENTS', 'APG ASSET MANAGEMENT N.V.',
                         'APG ASSET MANAGEMENT US INC.');
-- expect UPDATE 613 (59 + 493 + 61) on the 2026-06-30 quarter
COMMIT;
```

(The BPL `stock_percent_ownership` null that earlier drafts had here is
**deliberately omitted** — not partner-requested; see § 6a.)

```sql
SELECT investor_name, investor_type, COUNT(*) FROM investment
 WHERE investor_name LIKE 'PGGM%' OR investor_name LIKE 'APG %' GROUP BY 1,2 ORDER BY 1;
```

Then persist the labels for future SEC refreshes:

```bash
psql -c "\copy (SELECT DISTINCT investor_name AS name FROM investment WHERE source = 'U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)' AND investor_type = 'PENSION FUND' ORDER BY 1) TO 'data/input/sec_pension_funds.csv' WITH (FORMAT csv, HEADER true)"
grep -c . data/input/sec_pension_funds.csv   # 31 = header + 30 names (27 before + 3)
```

### 8.3 NBIM (15 min)

**Schema fix first (one-time).** `stock_percent_ownership` and
`stock_percent_voting_power` are `numeric(6,5)`, which caps at 9.99999 %.
Norges Bank owns 23.45 % of Shaftesbury Capital and 12.21 % of Vonovia, so the
COPY fails with `numeric field overflow` at line 5525. Widen both columns
before loading. Nothing in prod depends on these columns (no views), but the
ALTER rewrites the 2.1 GB table under an exclusive lock — expect 1–3 minutes
during which site queries wait. If a load transaction is open and aborted
(`postgres=!>` prompt), `ROLLBACK;` first.

```sql
ALTER TABLE investment
  ALTER COLUMN stock_percent_ownership TYPE numeric(8,5),
  ALTER COLUMN stock_percent_voting_power TYPE numeric(8,5);
SELECT column_name, numeric_precision, numeric_scale FROM information_schema.columns
 WHERE table_name = 'investment' AND column_name LIKE 'stock_percent%';
-- expect precision 8, scale 5 for both
```

```bash
export NBIM_DATE=2026-06-30
ls data/input/nbim_equity_${NBIM_DATE}.csv
(cd manual && python main.py --nbim-only --nbim-report-date "$NBIM_DATE")
mv data/output/shareholder_tracker_release_$(date -u +%Y%m%d).csv data/output/nbim_${NBIM_DATE}.csv
python manual/validate_release.py data/output/nbim_${NBIM_DATE}.csv --targets manual/validation_targets_2026-11.csv
```

Validator must print **7,077 rows, 1,660.9 bn, PASS, exit 0**. Then:

```sql
BEGIN;
DELETE FROM investment WHERE source = 'NORGES BANK';
-- expect DELETE 8374
\copy investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date) FROM 'data/output/nbim_2026-06-30.csv' WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL');
-- expect COPY 7077
COMMIT;
SELECT COUNT(*), MIN(document_report_date), ROUND(SUM(security_market_value_amount_usd)/1e9,1) AS usd_bn,
       COUNT(*) FILTER (WHERE stock_percent_ownership IS NOT NULL) AS with_ownership
  FROM investment WHERE source = 'NORGES BANK';
-- expect 7077 | 2026-06-30 | 1660.9 | 6934
```

### 8.4 Pension workbook (15 min)

```bash
(cd manual && python main.py --pension-only --pension-file ../data/input/pension_funds_2026-11-10.xlsx)
mv data/output/shareholder_tracker_release_$(date -u +%Y%m%d).csv data/output/pension_2026-11-10.csv
python manual/validate_release.py data/output/pension_2026-11-10.csv --targets manual/validation_targets_2026-11.csv
```

Validator must print **27,114 rows, 15 sources, every USD fund PASS, exit 0**
(AMF/AP4/KPA show `n/a` — no values by design). Per-tab log lines should
report the drops in § 4: AMF 6 dups, bpfBOUW 3 subtotals, LACERA 9 dups + 10
blank issuers + 103 ISINs blanked, PME 2, Rail & OV 1, Vervoer 5. Then:

```sql
BEGIN;
DELETE FROM investment WHERE source IN (
  'AMF PENSIONSFÖRSÄKRING AB', 'ANDRA AP-FONDEN', 'TREDJE AP-FONDEN',
  'FJÄRDE AP-FONDEN', 'SJUNDE AP-FONDEN', 'BOUWNIJVERHEID',
  'DANICA PENSION LIVSFORSIKRINGS AB', 'KPA PENSIONSFORSAKRING',
  'PENSIONDANMARK PENSIONSFORSIKRING A/S', 'PENSIONSKASSERNES ADMINISTRATION A/S',
  'PENSIOENFONDS VAN DE METALEKTRO', 'PENSIOENFONDS VERVOER');
-- expect DELETE 18674
\copy investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date) FROM 'data/output/pension_2026-11-10.csv' WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL');
-- expect COPY 27114
COMMIT;
```

### 8.5 Final verification (5 min)

```sql
SELECT source, COUNT(*) AS rows, ROUND(SUM(security_market_value_amount_usd)/1e9,1) AS usd_bn,
       MIN(document_report_date) AS report_date, COUNT(DISTINCT investor_name) AS names
  FROM investment GROUP BY source ORDER BY rows DESC;
```

| source | rows | usd_bn | report_date |
|---|---|---|---|
| U.S. SECURITIES AND EXCHANGE COMMISSION (SEC) | 1,932,680 (unchanged) | 58,002.4 | 2026-06-30 |
| NORGES BANK | 7,077 | 1,660.9 | 2026-06-30 |
| LOS ANGELES COUNTY EMPLOYEES RETIREMENT ASSOCIATION | 5,725 | 29.5 | 2025-09-30 |
| PENSIOENFONDS ZORG EN WELZIJN | 5,428 (unchanged) | 189.3 | 2024-12-31 |
| STICHTING BPL PENSIOEN | 4,672 (unchanged) | 6.6 | 2023-12-31 |
| BOUWNIJVERHEID | 4,225 | 15.5 | 2025-12-31 |
| DANICA PENSION LIVSFORSIKRINGS AB | 2,390 | 34.3 | 2025-12-31 |
| STICHTING PENSIOENFONDS ABP | 2,019 (unchanged) | 142.6 | 2025-06-30 |
| SJUNDE AP-FONDEN | 1,913 | 134.4 | 2025-12-31 |
| PENSIONSKASSERNES ADMINISTRATION A/S | 1,660 | 12.7 | 2026-05-31 |
| PENSIONDANMARK PENSIONSFORSIKRING A/S | 1,591 | 20.5 | 2025-12-31 |
| PENSIOENFONDS METAAL EN TECHNIEK | 1,384 | 23.2 | 2026-03-31 |
| PENSIOENFONDS VAN DE METALEKTRO | 1,360 | 18.7 | 2026-04-30 |
| FJÄRDE AP-FONDEN | 1,306 | (null) | 2025-12-31 |
| ANDRA AP-FONDEN | 1,288 | 19.4 | 2025-12-31 |
| PENSIOENFONDS VERVOER | 1,269 | 12.4 | 2025-12-31 |
| SAMPENSION ADMINISTRATIONSSELSKAB A/S | 1,181 (unchanged) | 9.4 | 2025-08-31 |
| TREDJE AP-FONDEN | 1,076 | 27.9 | 2025-12-31 |
| PENSIOENFONDS RAIL & OV | 1,052 | 8.8 | 2025-03-31 |
| KPA PENSIONSFORSAKRING | 552 | (null) | 2026-02-26 |
| AMF PENSIONSFÖRSÄKRING AB | 323 | (null) | 2025-12-31 |

21 sources, **1,980,171 rows** (= 1,973,028 − 8,374 − 18,674 + 7,077 + 27,114).
`names` must be 1 for every non-SEC source. Spot-check on the live site: the
Norges Bank page shows NVIDIA with an ownership sentence; a LACERA search
returns results under the Pension Funds filter; PGGM appears under Pension
Funds; AP2 shows a single abbreviation.

### 8.6 Downloads page (30 min, manual upload)

```bash
python manual/export_release.py --release-date 2026-11-10
```

Counts printed must equal § 8.5. Upload the `.zip`, `.parquet`, `.sqlite.gz`
from `data/output/2026-11-10/` to the R2 bucket under `2026-11-10/` and add the
entry to `web/config/downloads.ts` — REFRESH.md § 2g has the dashboard /
wrangler steps and the verification curl. Note in the release entry that AP4
has no market values and Sampension is on its 2025-08-31 list, pending
re-scrapes.

### 8.7 About page (deploy)

Apply § 6b to `web/app/about/page.tsx` (beads issue
`idi-shareholder-tracker-6gi`), open/merge the PR; Vercel deploys on merge to
`main`. Do this only after § 8.5 passes — the text names funds that exist only
after the loads.

### 8.8 Rollback (per block)

The backup table from § 8.1 restores any source independently:

```sql
BEGIN;
DELETE FROM investment WHERE source IN ('<source>', ...);
INSERT INTO investment (source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date)
SELECT source, document_report_date, document_filing_date, investor_type, investor_cik, investor_name, investor_abbreviation, investor_country_name, investor_country_code, investor_region_name, investor_region_code, issuer_name, issuer_country_name, issuer_country_code, issuer_sector, security_type, security_vintage_year, security_principal_amount_currency_code, security_principal_amount, security_market_value_currency_code, security_market_value_amount, security_market_value_multiplier, security_market_value_conversion_rate, security_market_value_amount_usd, security_isin, security_cusip, security_figi, stock_ticker, stock_number_of_shares, stock_percent_ownership, stock_percent_voting_power, stock_voting_auth_sole, stock_voting_auth_shared, stock_voting_auth_none, url, text, last_accessed_date
  FROM investment_backup_20261110 WHERE source IN ('<source>', ...);
COMMIT;
```

For § 8.2, the inverse is `UPDATE … SET investor_type = 'INSTITUTIONAL
INVESTOR'` for the three names. Drop the backup table once the release has
been live for a few weeks.
