// Third-party imports
import type { Metadata } from "next";

// Application imports
import { bebasNeue, geistMono, geistSans, montserrat } from "@/config/fonts";
import { Providers } from "./providers";

// Style imports
import "./globals.css";

export const metadata: Metadata = {
  title: "Shareholder Tracker - Inclusive Development International",
  description: "An online database of institutional investments.",
};

/**
 * The root layout component for the application. Sets up the HTML structure, imports global CSS, and wraps the children in a provider component.
 *
 * @param props - The component props.
 * @param props.children - The children of the component.
 *
 * @returns - The wrapped component.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          defer
          src="https://core-facility-umami.vercel.app/script.js"
          data-website-id="7bfbdbc9-d5ce-4b21-b252-4c9edcd7f948"
        ></script>
      </head>
      <body
        className={`${bebasNeue.variable} ${geistSans.variable} ${geistMono.variable} ${montserrat.variable} bg:white antialiased dark:bg-black`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
