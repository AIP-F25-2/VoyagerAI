/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:5000/api/:path*",
      },
    ];
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "s1.ticketm.net" },
      { protocol: "https", hostname: "img.evbuc.com" },
      { protocol: "https", hostname: "cdn.evbstatic.com" },
    ],
  },
};

module.exports = nextConfig;
