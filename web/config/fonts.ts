// Third-party imports
import { Bebas_Neue, Geist, Geist_Mono, Montserrat } from "next/font/google";

/**
 * The Bebas Neue font.
 * See: https://fonts.google.com/specimen/Bebas+Neue
 */
export const bebasNeue = Bebas_Neue({
  weight: "400",
  variable: "--font-bebas-neue",
});

/**
 * The Geist Sans font.
 * See: https://fonts.google.com/specimen/Geist
 */
export const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

/**
 * The Geist Mono font.
 * See: https://fonts.google.com/specimen/Geist+Mono
 */
export const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

/**
 * The Montserrat font.
 * See: https://fonts.google.com/specimen/Montserrat
 */
export const montserrat = Montserrat({
  weight: ["400", "700", "800"],
  variable: "--font-montserrat",
});
