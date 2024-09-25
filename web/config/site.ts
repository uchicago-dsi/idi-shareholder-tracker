export type SiteConfig = typeof siteConfig;

export const siteConfig = {
  name: "Shareholder Tracker - IDI",
  description: "Trace institional investments disclosed in 13F filings.",
  navItems: [
    {
      label: "Home",
      href: "/",
    },
  ],
  navMenuItems: [],
  links: {
    github: "https://github.com/uchicago-dsi/idi-shareholder-tracker",
  },
};
