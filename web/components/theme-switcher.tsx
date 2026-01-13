"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Button } from "@heroui/react";
import { MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";

// Application imports
import { useMounting } from "@/hooks/use-mounting";

/**
 * A set of two buttons for toggling between light and dark site themes.
 * Waits for the component to mount before rendering the button row,
 * as required by the next-theme package's {@link useTheme} hook.
 *
 * @returns The JSX element.
 */
export const ThemeSwitcher: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { mounted } = useMounting();
  return !mounted ? null : (
    <div>
      <Button
        isIconOnly
        className="bg-transparent"
        onPress={() => setTheme("dark")}
        hidden={theme === "dark"}
      >
        <MoonIcon fill="#8d8a8a" color="lightgray" strokeWidth={1} size={26} />
      </Button>
      <Button
        isIconOnly
        className="bg-transparent"
        onPress={() => setTheme("light")}
        hidden={theme === "light"}
      >
        <SunIcon fill="#8d8a8a" color="lightgray" strokeWidth={1} size={26} />
      </Button>
    </div>
  );
};
