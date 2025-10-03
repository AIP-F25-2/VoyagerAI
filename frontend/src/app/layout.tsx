import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import styles from "./layout.module.css";

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
        <div className={styles.wrapper}>
          <header className={styles.header}>
            <div className={styles.container}>
              <div className={styles.brand}>
                <span className={styles.logo}>V</span>
                <span>VoyagerAI</span>
              </div>
              <nav className={styles.nav}>
                <a href="#">Events</a>
                <a href="#">Planner</a>
                <a href="#">About</a>
                <a href="/login">Login</a>
                <a href="/signup">Sign up</a>
              </nav>
            </div>
          </header>
          <main className={styles.main}>{children}</main>
          <footer className={styles.footer}>
            <div className={styles.footerInner}>
              <span>© {new Date().getFullYear()} VoyagerAI</span>
              <span className="hide-sm">Built with Next.js</span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
