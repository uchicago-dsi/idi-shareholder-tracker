"use client";

// Standard library imports
import React, { useEffect, useState } from "react";

// Third-party imports
import { Button } from "@heroui/react";
import { MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";

/**
 * A set of two buttons for toggling between light and dark site themes.
 *
 * @returns - The JSX element.
 */
export const ThemeSwitcher: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []); // eslint-disable react-hooks/exhaustive-deps

  if (!mounted) return null;

  return (
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
