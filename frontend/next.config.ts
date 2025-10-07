/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "s1.ticketm.net", // Ticketmaster images
      },
      {
        protocol: "https",
        hostname: "img.evbuc.com", // Eventbrite images
      },
      {
        protocol: "https",
        hostname: "cdn.evbstatic.com", // extra Eventbrite host
      },
    ],
  },
};

module.exports = nextConfig;
