// Standard library imports
import { useEffect, useState } from "react";

type UseDelayedItemReturn<T> = {
  item: T;
};

/**
 * A hook to cycle through a generic list of items while using the given delay.
 *
 * @param items - The list of items to cycle through.
 * @param delay - The delay in milliseconds between each item. Defaults to 2000.
 *
 * @returns The current item in the cycle.
 */
export function useDelayedItem<T>(
  items: T[],
  delay: number = 2000,
): UseDelayedItemReturn<T> {
  const [itemIdx, setItemIdx] = useState<number>(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setItemIdx((prevIndex) => (prevIndex + 1) % items.length);
    }, delay);
    return () => clearInterval(interval);
  }, [items.length, delay]);

  return {
    item: items[itemIdx],
  };
}
