"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Link } from "@heroui/react";
import Image from "next/image";

// Application imports
import { GitHubIcon } from "@/components/icons";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { SITE_CONFIG } from "@/config/site";

/**
 * A component that renders a navbar with a link to the Github repository and a theme switcher.
 *
 * @returns - A JSX element representing the navbar.
 */
export const Navbar: React.FC = () => {
  return (
    <div className="m-auto flex w-full flex-row justify-center pt-4">
      <div className="flex w-full max-w-7xl flex-row items-start justify-between px-8">
        <div>
          <Image
            className="light:block cursor-pointer hover:opacity-90 dark:hidden"
            alt="IDI Logo"
            src="/idi-logo-light.webp"
            height={125}
            width={125}
            onClick={() => window.open(SITE_CONFIG.footerLinks.idi, "_blank")}
          />
          <Image
            className="hidden cursor-pointer hover:opacity-90 dark:block"
            alt="IDI Logo"
            src="/idi-logo-dark.webp"
            height={125}
            width={125}
            onClick={() => window.open(SITE_CONFIG.footerLinks.idi, "_blank")}
          />
        </div>
        <div className="flex flex-row items-center">
          <Link
            aria-label="Github"
            href={SITE_CONFIG.navbarLinks.github}
            target="_blank"
            underline="none"
          >
            <GitHubIcon
              className="hover:opacity-0.7 text-neutral-400"
              size={30}
            />
          </Link>
          <ThemeSwitcher />
        </div>
      </div>
    </div>
  );
};
