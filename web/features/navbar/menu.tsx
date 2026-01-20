"use client";

// Standard library imports
import React from "react";

// Third-party imports
import {
  Button,
  Link,
  Listbox,
  ListboxItem,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  useDisclosure,
} from "@heroui/react";
import {
  BookOpenIcon,
  CloudDownloadIcon,
  DatabaseIcon,
  MenuIcon,
  XIcon,
} from "lucide-react";
import { usePathname } from "next/navigation";

// Application imports
import { GitHubIcon } from "@/components/icons";

// Feature imports
import { DesktopThemeSwitcher, MobileThemeSwitcher } from "./theme-switcher";

/**
 * A desktop-only navigation menu with links to the database, downloads, about and Github pages.
 *
 * @returns A JSX element representing the navigation bar.
 */
export const DesktopMenu: React.FC = () => {
  const pathName = usePathname();
  return (
    <div className="hidden flex-row items-center gap-4 lg:flex">
      <Link
        aria-label="Database page"
        href="/"
        underline="none"
        className={`font-bebas-neue text-2xl leading-none text-black uppercase dark:text-white ${pathName === "/" ? "decoration-seagreen underline underline-offset-8" : ""}`}
      >
        Database
      </Link>
      <Link
        aria-label="Downloads page"
        href="/downloads"
        underline="none"
        className={`font-bebas-neue text-2xl leading-none text-black uppercase dark:text-white ${pathName === "/downloads" ? "decoration-seagreen underline underline-offset-8" : ""}`}
      >
        Downloads
      </Link>
      <Link
        aria-label="About page"
        href="/about"
        underline="none"
        className={`font-bebas-neue text-2xl leading-none text-black uppercase dark:text-white ${pathName === "/about" ? "decoration-seagreen underline underline-offset-8" : ""}`}
      >
        About
      </Link>
      <DesktopThemeSwitcher />
    </div>
  );
};

/**
 * A mobile-only navigation menu that displays a list of links to
 * the database, bulk downloads, and about pages. The menu is
 * represented by a hamburger menu icon that launches a full-screen
 * modal when clicked.
 *
 * @returns A JSX element representing the navigation bar.
 */
export const MobileMenu: React.FC = () => {
  const pathName = usePathname();
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <div className="lg:hidden">
      {/** TRIGGER BUTTON */}
      <Button
        isIconOnly
        className="flex flex-row justify-end bg-transparent"
        onPress={() => onOpen()}
      >
        <MenuIcon size={24} className="dark:text-white" />
      </Button>

      {/** CONTENT MODAL */}
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size="full"
        classNames={{
          closeButton: "hidden",
        }}
      >
        <ModalContent>
          {() => (
            <>
              {/** HEADER */}
              <ModalHeader className="dark:bg-default-50 font-bebas-neue flex flex-col">
                <div className="flex flex-row items-start justify-between">
                  <p className="text-4xl font-normal">Shareholder Tracker</p>
                  <Button
                    isIconOnly
                    onPress={() => onClose()}
                    className="flex h-8 min-h-8 w-8 min-w-8 flex-row justify-end bg-transparent"
                  >
                    <XIcon
                      strokeWidth={4}
                      className="dark:text-white"
                      size={24}
                    />
                  </Button>
                </div>
              </ModalHeader>

              {/** BODY */}
              <ModalBody>
                <Listbox className="font-montserrat">
                  {/** DATABASE LINK */}
                  <ListboxItem
                    href="/"
                    className={`rounded-none py-3 ${pathName === "/" ? "border-seagreen border-l-4" : ""}`}
                  >
                    <p className="flex flex-row gap-2 text-base font-bold text-black dark:text-white">
                      <DatabaseIcon size={20} />
                      Database
                    </p>
                    <p className="text-sm">
                      Search 2M+ investments disclosed by pension funds and
                      institutional investors.
                    </p>
                  </ListboxItem>

                  {/** DOWNLOADS LINK */}
                  <ListboxItem
                    href="/downloads"
                    className={`rounded-none py-3 ${pathName === "/downloads" ? "border-seagreen border-l-4" : ""}`}
                  >
                    <p className="font-montserrat flex flex-row gap-2 text-base font-bold text-black dark:text-white">
                      <CloudDownloadIcon size={20} />
                      Bulk Downloads
                    </p>
                    <p className="font-montserrat text-sm">
                      Download the datasets used to build the site in CSV,
                      Parquet, or SQLite format.
                    </p>
                  </ListboxItem>

                  {/** ABOUT LINK */}
                  <ListboxItem
                    href="/about"
                    className={`rounded-none py-3 ${pathName === "/about" ? "border-seagreen border-l-4" : ""}`}
                  >
                    <p className="font-montserrat flex flex-row gap-2 text-base font-bold text-black dark:text-white">
                      <BookOpenIcon size={20} />
                      About
                    </p>
                    <p className="font-montserrat text-sm">
                      Learn about the purpose of the site and the methodology
                      used for data collection.
                    </p>
                  </ListboxItem>

                  {/** CONTRIBUTE LINK */}
                  <ListboxItem
                    href="https://github.com/uchicago-dsi/idi-shareholder-tracker"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <p className="font-montserrat flex flex-row gap-2 text-base font-bold text-black dark:text-white">
                      <GitHubIcon size={20} />
                      Contribute
                    </p>
                    <p className="font-montserrat flex flex-row text-sm">
                      View the source code and contribute to the project on
                      GitHub.
                    </p>
                  </ListboxItem>
                </Listbox>
              </ModalBody>

              {/** FOOTER */}
              <ModalFooter>
                <MobileThemeSwitcher />
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
};
