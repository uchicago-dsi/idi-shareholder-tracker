"use client";

// Standard library imports
import React from "react";

// Third-paty imports
import { Link } from "@heroui/react";
import Image from "next/image";

// Application imports
import { SITE_CONFIG } from "@/config/site";

/**
 * A footer component that displays site acknowledgments, quick links, and partner logos.
 *
 * @returns A JSX element representing the footer.
 */
export const Footer: React.FC = () => {
  return (
    <footer className="bg-forest flex flex-col gap-4 text-white">
      <div className="flex flex-col items-center gap-10 p-6 lg:mx-auto lg:mt-5 lg:grid lg:max-w-7xl lg:grid-cols-3 lg:flex-row lg:items-start">
        {/** ACKNOWLEDGMENTS */}
        <div className="flex flex-col items-center gap-4 text-center">
          <h4 className="bg-seagreen font-bebas-neue px-4 py-2 text-xl uppercase">
            Acknowledgments
          </h4>
          <p className="font-montserrat text-sm">
            {SITE_CONFIG.acknowledgments}
          </p>
        </div>

        {/** QUICK LINKS */}
        <div className="flex flex-col items-center gap-4">
          <h4 className="font-bebas-neue text-xl uppercase">Quick Links</h4>
          <div className="flex flex-col items-center gap-2">
            {SITE_CONFIG.footerLinks.quick.map((link, idx) => (
              <Link
                key={idx}
                href={link.url}
                className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
                isExternal
                showAnchorIcon
              >
                {link.text}
              </Link>
            ))}
          </div>
        </div>

        {/** PARTNERS */}
        <div className="flex flex-col items-center gap-4">
          <h4 className="font-bebas-neue text-xl uppercase">Partners</h4>
          <Image
            className="cursor-pointer hover:opacity-90"
            alt="IDI Logo"
            src="/idi-logo-dark.webp"
            height={150}
            width={150}
            onClick={() => window.open(SITE_CONFIG.footerLinks.idi, "_blank")}
          />
          <Image
            className="cursor-pointer rounded-xl border bg-white p-2 hover:opacity-90"
            alt="IDI Logo"
            src="/uchicago-dsi-logo.png"
            height={150}
            width={250}
            onClick={() =>
              window.open(SITE_CONFIG.footerLinks.uchicagoDsi, "_blank")
            }
          />
        </div>
      </div>

      {/** COPYRIGHT */}
      <div className="bg-seagreen font-montserrat w-full p-4 text-center text-sm">
        <h6>
          &copy; {new Date().getFullYear()} Inclusive Development International
        </h6>
      </div>
    </footer>
  );
};
