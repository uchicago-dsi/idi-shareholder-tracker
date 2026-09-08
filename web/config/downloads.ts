/**
 * The download/release configuration.
 */
export const DOWNLOAD_CONFIG = [
  {
    date: "September 8, 2026",
    dataDictionaryUrl:
      "https://shareholder-tracker.cdn.uchicago-dsi.org/2025-12-18/shareholder_tracker_data_dictionary_20251218.pdf",
    files: [
      {
        type: "CSV",
        url: "https://shareholder-tracker.cdn.uchicago-dsi.org/2026-09-08/shareholder_tracker_release_20260908.zip",
        size: "109 MB",
      },
      {
        type: "PARQUET",
        url: "https://shareholder-tracker.cdn.uchicago-dsi.org/2026-09-08/shareholder_tracker_release_20260908.parquet",
        size: "134 MB",
      },
      {
        type: "SQLITE",
        url: "https://shareholder-tracker.cdn.uchicago-dsi.org/2026-09-08/shareholder_tracker_release_20260908.sqlite.gz",
        size: "132 MB",
      },
    ],
  },
  {
    date: "December 18, 2025",
    dataDictionaryUrl:
      "https://shareholder-tracker.cdn.uchicago-dsi.org/2025-12-18/shareholder_tracker_data_dictionary_20251218.pdf",
    files: [
      {
        type: "CSV",
        url: "https://shareholder-tracker.cdn.uchicago-dsi.org/2025-12-18/shareholder_tracker_release_20251218.zip",
        size: "122 MB",
      },
      {
        type: "PARQUET",
        url: "https://shareholder-tracker.cdn.uchicago-dsi.org/2025-12-18/shareholder_tracker_release_20251218.parquet",
        size: "154 MB",
      },
      {
        type: "SQLITE",
        url: "https://shareholder-tracker.cdn.uchicago-dsi.org/2025-12-18/shareholder_tracker_release_20251218.sqlite.gz",
        size: "150 MB",
      },
    ],
  },
];

export type DownloadConfig = typeof DOWNLOAD_CONFIG;
