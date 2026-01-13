// Standard library imports
import React from "react";

// Application imports
import { SITE_CONFIG } from "@/config/site";

// Feature imports
import { Footer } from "@/features/footer";
import { InvestmentSearchWidget } from "@/features/investments";
import { Navbar } from "@/features/navbar";

/**
 * The application homepage. Renders a navigation bar, title and subtitle, description, search widget, and footer.
 */
const Home: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center font-sans">
      {/** NAVIGATION BAR */}
      <Navbar />
      <div className="flex min-h-screen w-full flex-col gap-8 pt-8">
        <main className="m-auto flex min-h-screen w-full max-w-7xl flex-col items-center gap-4 px-8 lg:gap-8">
          {/** TITLE BLOCK */}
          <div className="flex flex-col items-center text-center">
            <h1 className="font-bebas-neue text-4xl lg:text-6xl">
              {SITE_CONFIG.title}
            </h1>
            <h2 className="font-montserrat text-zinc-500 lg:text-xl dark:text-zinc-400">
              {SITE_CONFIG.subtitle}
            </h2>
          </div>

          {/** DESCRIPTION BLOCK */}
          <div className="font-montserrat flex flex-col gap-2 text-sm lg:text-base">
            {SITE_CONFIG.description.map((paragraph, idx) => (
              <p key={idx}>{paragraph}</p>
            ))}
          </div>

          {/** SEARCH WIDGET */}
          <InvestmentSearchWidget tableConfig={SITE_CONFIG.table} />
        </main>

        {/** FOOTER */}
        <Footer />
      </div>
    </div>
  );
};

export default Home;
