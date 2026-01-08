"use client";

// Standard library imports
import React, { PropsWithChildren } from "react";

// Third-party imports
import { HeroUIProvider } from "@heroui/react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

/**
 * Context providers to use at the root of the application.
 * Includes {@link HeroUIProvider} and {@link NextThemesProvider}.
 *
 * @param {children} - The children of the component.
 *
 * @returns {JSX.Element} - The wrapped component.
 */
export const Providers: React.FC<PropsWithChildren> = ({ children }) => {
  return (
    <HeroUIProvider>
      <NextThemesProvider attribute="class" defaultTheme="light">
        {children}
      </NextThemesProvider>
    </HeroUIProvider>
  );
};
