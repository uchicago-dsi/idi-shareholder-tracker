// Standard library imports
import React from "react";

// Third-party imports
import { TriangleAlertIcon } from "lucide-react";

/**
 * A component that displays an error message.
 *
 * @returns A JSX element representing an error message.
 */
export const ErrorMessage: React.FC = () => {
  return (
    <div className="bg-default-100 flex w-full flex-col items-center justify-center gap-2 p-5 lg:flex-row lg:items-end lg:p-10">
      <TriangleAlertIcon className="h-8 w-8 text-red-400 dark:text-red-200" />
      <p className="font-montserrat text-center text-sm font-bold text-red-500 lg:text-left lg:text-lg dark:text-red-200">
        An unexpected error occurred while loading the data. Please refresh the
        page or try again later.
      </p>
    </div>
  );
};
