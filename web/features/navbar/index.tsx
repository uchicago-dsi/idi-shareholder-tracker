"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Link } from "@heroui/react";

// Feature imports
import { DesktopMenu, MobileMenu } from "./menu";

/**
 * A component that renders a navbar with a link to the Github repository and a theme switcher.
 *
 * @returns - A JSX element representing the navbar.
 */
export const Navbar: React.FC = () => {
  return (
    <div className="m-auto flex w-full flex-row justify-center pt-4">
      <div className="flex w-full max-w-7xl flex-row items-center justify-between px-8 lg:items-start">
        <div className="flex flex-col gap-0">
          <Link
            className="font-bebas-neue bg-seagreen rounded-md px-2 pt-2 pb-1 text-4xl text-white"
            href="/"
          >
            ST
          </Link>
        </div>
        <DesktopMenu />
        <MobileMenu />
      </div>
    </div>
  );
};
