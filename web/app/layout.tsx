// Third-party imports
import type { Metadata } from "next";

// Style imports
import "./globals.css";

// Application imports
import { bebasNeue, montserrat } from "@/config/fonts";
import { Providers } from "./providers";

// Feature imports
import { Navbar } from "@/features/navbar";
import { Footer } from "@/features/footer";

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
        className={`${bebasNeue.variable} ${montserrat.variable} bg-white antialiased dark:bg-black`}
      >
        <Providers>
          <div className="flex min-h-screen flex-col items-center font-sans">
            <Navbar />
            <div className="flex min-h-screen w-full flex-col gap-8 pt-8">
              <main className="m-auto flex w-full max-w-7xl flex-col items-center gap-4 px-8 pb-8 lg:gap-8">
                {children}
              </main>
              <Footer />
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
