"use client";

// Standard library imports
import React from "react";

// Third-paty imports
import { Link } from "@heroui/react";
import Image from "next/image";

/**
 * A footer component that displays site acknowledgments, quick links, and partner logos.
 *
 * @returns A JSX element representing the footer.
 */
export const Footer: React.FC = () => {
  return (
    <footer className="bg-forest flex flex-col gap-4 text-white">
      <div className="flex flex-col items-center gap-10 p-6 lg:mx-auto lg:mt-5 lg:grid lg:max-w-7xl lg:grid-cols-4 lg:flex-row lg:items-start">
        {/** ACKNOWLEDGMENTS */}
        <div className="flex flex-col items-center gap-4 text-center lg:items-start lg:text-left">
          <h4 className="bg-seagreen font-bebas-neue px-4 py-2 text-xl uppercase">
            Acknowledgments
          </h4>
          <p className="font-montserrat text-sm">
            The Shareholder Tracker was developed in 2025 through a partnership
            between Inclusive Development International and the University of
            Chicago Data Science Institute, with funding generously provided by
            the 11th Hour Project of the Schmidt Family Foundation.
          </p>
        </div>

        {/** QUICK LINKS */}
        <div className="flex flex-col items-center gap-4 lg:ml-10 lg:items-start">
          <h4 className="font-bebas-neue text-left text-xl uppercase">
            Quick Links
          </h4>
          <div className="flex flex-col items-center gap-1 lg:items-start">
            <Link
              href="/"
              className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
            >
              Database
            </Link>
            <Link
              href="/downloads"
              className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
            >
              Downloads
            </Link>
            <Link
              href="/about"
              className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
            >
              About
            </Link>
            <Link
              href="https://github.com/uchicago-dsi/idi-shareholder-tracker"
              className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
              isExternal
              showAnchorIcon
            >
              Contribute
            </Link>
          </div>
        </div>

        {/** RELATED PROJECTS */}
        <div className="flex flex-col items-center gap-4 lg:ml-10 lg:items-start">
          <h4 className="font-bebas-neue text-left text-xl uppercase">
            Related Projects
          </h4>
          <div className="flex flex-col items-center gap-1 lg:items-start">
            <Link
              href="https://debit.datascience.uchicago.edu/"
              className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
              isExternal
              showAnchorIcon
            >
              DeBIT
            </Link>
            <Link
              href="https://palmwatch.inclusivedevelopment.net/"
              className="font-montserrat inline-flex items-center gap-2 text-white uppercase"
              isExternal
              showAnchorIcon
            >
              PalmWatch
            </Link>
          </div>
        </div>

        {/** PARTNERS */}
        <div className="flex flex-col items-center gap-4 lg:items-start">
          <h4 className="font-bebas-neue text-xl uppercase">Partners</h4>
          <Image
            className="cursor-pointer hover:opacity-90"
            alt="IDI Logo"
            src="/idi-logo-dark.webp"
            height={150}
            width={150}
            onClick={() =>
              window.open("https://www.inclusivedevelopment.net/", "_blank")
            }
          />
          <Image
            className="cursor-pointer rounded-xl border bg-white p-2 hover:opacity-90"
            alt="UChicago DSI Logo"
            src="/uchicago-dsi-logo.png"
            height={150}
            width={250}
            onClick={() =>
              window.open("https://datascience.uchicago.edu/", "_blank")
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
