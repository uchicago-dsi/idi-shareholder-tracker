// Standard library imports
import React from "react";

// Third-party imports
import { Spinner } from "@heroui/react";

// Application imports
import { useDelayedItem } from "@/hooks/use-delayed-item";

type LoadingSpinnerProps = {
  messages: string[];
};

/**
 * A component that displays a loading spinner with a delayed cycling of messages.
 *
 * @param props - The component props.
 * @param props.messages - An array of messages to cycle through.
 *
 * @returns A JSX element representing the loading spinner and delayed messages.
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ messages }) => {
  const { item: message } = useDelayedItem(messages);
  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <Spinner size="lg" color="success" />
      <span className="text-muted font-montserrat text-xl">{message}</span>
    </div>
  );
};
