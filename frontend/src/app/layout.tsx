import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import styles from "./layout.module.css";
import { AuthProvider } from "@/contexts/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VoyagerAI | Events Explorer",
  description: "Discover and manage events with VoyagerAI's smart scraper",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased ${styles.body}`}>
        <AuthProvider>
          <div className={styles.wrapper}>
            <main className={styles.main}>{children}</main>
            <footer className={styles.footer}>
              <div className={styles.footerInner}>
                <span>© {new Date().getFullYear()} VoyagerAI</span>
                <span className="hide-sm">Built with Next.js</span>
              </div>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
