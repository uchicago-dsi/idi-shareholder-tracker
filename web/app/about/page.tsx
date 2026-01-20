"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Link } from "@heroui/link";
import { ExternalLink } from "lucide-react";

/**
 * The about page.
 */
const About: React.FC = () => {
  return (
    <>
      {/** TITLE BLOCK */}
      <div className="flex w-full flex-col items-center text-center">
        <h1 className="font-bebas-neue text-4xl lg:text-6xl">About</h1>
      </div>

      {/** DESCRIPTION */}
      <div className="font-montserrat flex flex-col gap-4 text-left text-sm lg:text-base">
        <p>
          The Shareholder Tracker is a collaborative project between{" "}
          <Link
            isExternal
            href="https://www.inclusivedevelopment.net/"
            className="decoration-seagreen inline text-sm font-bold text-black underline underline-offset-4 lg:text-base dark:text-white dark:decoration-green-300"
          >
            Inclusive Development International (IDI)
            <ExternalLink className="inline h-3.5" />
          </Link>{" "}
          and the{" "}
          <Link
            isExternal
            href="https://datascience.uchicago.edu/"
            className="decoration-seagreen inline text-sm font-bold text-black underline underline-offset-4 lg:text-base dark:text-white dark:decoration-green-300"
          >
            University of Chicago Data Science Institute (DSI)
            <ExternalLink className="inline h-3.5" />
          </Link>
          . It is designed to help civil society organizations uncover the
          shareholders of publicly traded companies. Shareholders are important
          campaign pressure points for advocates working to defend the rights of
          people and protect the environment.
        </p>
        <p>
          For advice on how to follow the money behind harmful investment
          projects—including how to uncover shareholders using other methods and
          target them in advocacy—see the{" "}
          <Link
            isExternal
            href="https://www.followingthemoney.org/"
            className="decoration-seagreen inline text-sm font-bold text-black underline underline-offset-4 lg:text-base dark:text-white dark:decoration-green-300"
          >
            Follow the Money to Justice
            <ExternalLink className="inline h-3.5 p-0" />
          </Link>{" "}
          website.
        </p>
        <p>The Shareholder Tracker scrapes data from the following sources:</p>
        <ul className="flex list-inside list-disc flex-col gap-4 px-2 pb-4">
          <li>
            The shareholdings of more than 4,200 institutional investors that
            are required to report to the U.S. Securities and Exchange
            Commission. These investors must file a 13F form disclosing their
            investments to the U.S. Securities and Exchange Commission because
            they have more than $100 million in assets under management and do
            business in the United States (note that they are not all based in
            the United States). This database scrapes those 13F forms on a
            quarterly basis, when they are required to be filed.
          </li>
          <li>
            The shareholdings of 17 European pension funds that do not report to
            the U.S. Securities and Exchange Commission. This database compiles
            information disclosed by the pension funds on their websites. The
            pension funds are: Norges Bank Investment Management, PME
            pensioenfonds, BPL Pensioen, PFZW, Tredje AP – Fonden, Sjunde
            AP-fonden, KPA Pensions, Pensionskassernes Administration, Pension
            Danmark, Sampension, Danica, Fjärde AP – Fonden, Stichting
            Pensioenfonds ABP, Andra AP-Fonden, bpf BOUW, Pensioenfonds Vervoer,
            and AMF Pension.
          </li>
        </ul>
        <p>
          This tool is a part of an open-source initiative at the Data Science
          Institute and will continue to be maintained by the DSI and
          contributors from around the world.
        </p>
      </div>
    </>
  );
};

export default About;
