// Standard library imports
import { useEffect, useState } from "react";

type UseMountingReturn = {
  mounted: boolean;
};

/**
 * A hook that returns a boolean indicating whether the current component has been mounted.
 *
 * Used prevent rendering of components that rely on the DOM being present.
 *
 * @returns An object containing the mounted state.
 */
export const useMounting = (): UseMountingReturn => {
  const [mounted, setMounted] = useState<boolean>(false);
  useEffect(() => {
    setMounted(true);
  }, []); // eslint-disable react-hooks/exhaustive-deps
  return { mounted };
};
