"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Button, Link } from "@heroui/react";
import { DownloadCloudIcon, DownloadIcon, ExternalLink } from "lucide-react";

// Application imports
import { DOWNLOAD_CONFIG } from "@/config/downloads";

interface File {
  type: string;
  url: string;
  size: string;
}

interface Release {
  date: string;
  dataDictionaryUrl: string;
  notes: string;
  files: File[];
}

type DataReleaseCardProps = {
  release: Release;
};

/**
 * A card that shows the date of the release and files available for download.
 *
 * @param props - The component props.
 * @param props.release - The release data object containing the date and a list of files.
 * @param props.release.date - The date of the release.
 * @param props.release.files - A list of file objects containing the type, url, and size of the file.
 */
const DataReleaseCard: React.FC<DataReleaseCardProps> = ({ release }) => {
  const getButtonColor = (type: string) => {
    if (type === "CSV") {
      return "primary";
    } else if (type === "PARQUET") {
      return "warning";
    } else {
      return "success";
    }
  };
  return (
    <div className="font-montserrat bg-default-100 flex flex-col gap-8 p-4">
      <div className="flex w-full flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
          <h2 className="text-lg font-bold">{release.date}</h2>
          <Button
            className="text-seagreen flex flex-row gap-2 bg-transparent p-0 font-bold uppercase dark:text-green-300"
            onPress={() => window.open(release.dataDictionaryUrl, "_blank")}
            startContent={<DownloadIcon className="inline h-5 stroke-3" />}
          >
            Data Dictionary
          </Button>
        </div>
        <div className="flex flex-col gap-2 font-bold lg:flex-row">
          {release.files.map((file, idx) => (
            <Button
              key={idx}
              color={getButtonColor(file.type)}
              size="lg"
              className="font-bold"
              variant="flat"
              onPress={() => window.open(file.url, "_blank")}
              startContent={<DownloadCloudIcon />}
            >
              <span className="font-bold">{file.type}</span>
              <span className="text-xs font-bold">{file.size}</span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * The bulk downloads page.
 */
const DownloadsPage: React.FC = () => {
  return (
    <div className="flex w-full flex-col gap-8">
      {/** TITLE BLOCK */}
      <div className="flex w-full flex-col items-center text-center">
        <h1 className="font-bebas-neue text-4xl lg:text-6xl">Bulk Downloads</h1>
      </div>

      {/** DESCRIPTION */}
      <div className="font-montserrat flex flex-col gap-2">
        <p>
          Download the data from the Shareholder Tracker here in CSV, Apache
          Parquet, and SQLite formats under a{" "}
          <Link
            isExternal
            href="https://creativecommons.org/licenses/by-nc-nd/4.0/"
            className="decoration-seagreen inline text-sm font-bold text-black underline underline-offset-4 lg:text-base dark:text-white dark:decoration-green-300"
          >
            CC BY-NC
            <ExternalLink className="inline h-3.5" />
          </Link>{" "}
          license. Please note that the CSV files are zipped and SQLlite files
          compressed with gzip, so they will need to be extracted and
          decompressed, respectively, before loading for analysis. At this time,
          company names have not been deduped through entity resolution but
          scraped from their original data sources as-is.
        </p>
      </div>

      {/** DOWNLOADS */}
      <div className="flex w-full flex-col gap-2">
        {DOWNLOAD_CONFIG.map((release, idx) => (
          <DataReleaseCard key={idx} release={release} />
        ))}
      </div>
    </div>
  );
};

export default DownloadsPage;
