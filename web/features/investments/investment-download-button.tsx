// Standard library imports
import React from "react";

// Third-party imports
import { Button, Spinner, Tooltip } from "@heroui/react";
import { FileDownIcon } from "lucide-react";

type InvestmentDownloadButtonProps = {
  isDownloading: boolean;
  handleDownload: () => void;
};

/**
 * A button component for downloading a list of investments in CSV format.
 * Displays a spinner when the download is in progress.
 *
 * @param props - The component props.
 * @param props.isDownloading - A boolean indicating whether the download is in progress.
 * @param props.handleDownload - A callback function to handle the download action.
 *
 * @returns The JSX element.
 */
export const InvestmentDownloadButton: React.FC<
  InvestmentDownloadButtonProps
> = ({ isDownloading, handleDownload }) => {
  return isDownloading ? (
    <Spinner size="lg" color="success" />
  ) : (
    <Tooltip
      closeDelay={0}
      content={
        <div className="font-montserrat m-0 flex max-w-[175px] flex-wrap rounded-xl p-2 text-xs">
          Download up to 10,000 investments as a CSV file
        </div>
      }
      placement="bottom"
    >
      <Button
        isIconOnly
        onPress={() => handleDownload()}
        className="bg-transparent"
      >
        <FileDownIcon
          size={32}
          className="stroke-seagreen stroke-[1.5px] dark:stroke-white"
        />
      </Button>
    </Tooltip>
  );
};
