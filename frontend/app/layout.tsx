import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoyagerAI Event Explorer",
  description: "Discover events powered by Ticketmaster API",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased bg-gray-900 text-gray-300" data-writer-injected="true">
        <header className="p-4 bg-blue-600 text-white">
          <h1 className="text-2xl font-bold">TEAM ODYSSEY | VoyagerAI</h1>
        </header>
        <main className="p-6">{children}</main>
        <footer className="mt-4 p-4 text-center text-sm text-gray-500">
          © {new Date().getFullYear()} VoyagerAI | Built by Team Odyssey @LCiT
        </footer>
      </body>
    </html>
  );
}
