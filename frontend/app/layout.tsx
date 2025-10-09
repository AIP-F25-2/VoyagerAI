import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/ui/Header";
import Footer from "@/components/ui/Footer";

export const metadata: Metadata = {
  title: "VoyagerAI Event Explorer",
  description: "Discover events powered by Ticketmaster & Eventbrite APIs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <Header />
        <main className="p-0 sm:p-6">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
