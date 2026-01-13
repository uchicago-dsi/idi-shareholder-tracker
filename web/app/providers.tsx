"use client";

// Standard library imports
import React, { PropsWithChildren } from "react";

// Third-party imports
import { HeroUIProvider } from "@heroui/react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

/**
 * Context providers to inject at the root of the application.
 * Includes {@link HeroUIProvider} and {@link NextThemesProvider}.
 *
 * @param props - The component props.
 * @param props.children - The children of the component.
 *
 * @returns The wrapped component.
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
