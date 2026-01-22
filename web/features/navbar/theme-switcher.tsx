"use client";

// Standard library imports
import React, { useState } from "react";

// Third-party imports
import { Button, cn, Switch } from "@heroui/react";
import { MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";

// Application imports
import { useMounting } from "@/hooks/use-mounting";

/**
 * A set of two buttons for toggling between light and dark site themes
 * on mobile devices. Waits for the component to mount before rendering
 * the button row, as required by the next-theme package's {@link useTheme} hook.
 *
 * @returns The JSX element.
 */
export const MobileThemeSwitcher: React.FC = () => {
  const { mounted } = useMounting();
  const { theme, setTheme } = useTheme();
  const [isSelected, setIsSelected] = useState<boolean>(theme === "dark");

  return (
    mounted && (
      <Switch
        aria-label="Mobile site theme toggle"
        isSelected={isSelected}
        onValueChange={(value) => {
          setIsSelected(value);
          setTheme(value ? "dark" : "light");
        }}
        className="lg:hidden"
        classNames={{
          base: cn(
            "inline-flex flex-row-reverse w-full max-w-md bg-content1 hover:bg-content2 items-center",
            "justify-between cursor-pointer rounded-lg gap-4 p-4 border-2 border-transparent",
            "border-seagreen",
          ),
          wrapper: "p-0 h-4 overflow-visible bg-seagreen dark:bg-seagreen",
          thumb: cn(
            "w-6 h-6 border-2 border-seagreen shadow-lg bg-white",
            "group-data-[selected=true]:ms-6",
            "group-data-[pressed=true]:w-7",
            "group-data-pressed:group-data-selected:ms-4",
          ),
        }}
        thumbIcon={isSelected ? <MoonIcon size={20} /> : <SunIcon size={20} />}
      >
        {isSelected ? (
          <div className="font-montserrat flex flex-col gap-1 text-white">
            <p className="font-bold">Dark Mode</p>
            <p className="text-sm">
              Saves power and reduces eye strain in low light conditions.
            </p>
          </div>
        ) : (
          <div className="font-montserrat flex flex-col gap-1 text-black">
            <p className="font-bold">Light Mode</p>
            <p className="text-sm">
              Reduces glare and maintains contrast in sunny conditions.
            </p>
          </div>
        )}
      </Switch>
    )
  );
};

/**
 * A set of two buttons for toggling between light and dark site themes
 * on desktop devices. Waits for the component to mount before rendering
 * the button row, as required by the next-theme package's {@link useTheme} hook.
 *
 * @returns The JSX element.
 */
export const DesktopThemeSwitcher: React.FC = () => {
  const { mounted } = useMounting();
  const { theme, setTheme } = useTheme();

  return (
    mounted && (
      <div
        className="hidden flex-row items-center lg:flex"
        aria-label="Desktop site theme toggle"
      >
        <Button
          isIconOnly
          className="h-8 w-8 min-w-8 rounded-full bg-transparent"
          onPress={() => setTheme("dark")}
          hidden={theme === "dark"}
        >
          <MoonIcon className="fill-seagreen stroke-white stroke-1" size={28} />
        </Button>
        <Button
          isIconOnly
          className="h-8 w-8 min-w-8 rounded-full bg-transparent"
          onPress={() => setTheme("light")}
          hidden={theme === "light"}
        >
          <SunIcon
            className="stroke-1 dark:fill-white dark:stroke-white"
            size={28}
          />
        </Button>
      </div>
    )
  );
};
