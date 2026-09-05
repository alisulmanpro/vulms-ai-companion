import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: "VULMS AI Companion — Smart LMS Alerts for VU Students",
  description:
    "Track VULMS assignments, quizzes, GDBs, and fee challans automatically. Get WhatsApp alerts before deadlines with the browser extension and web dashboard.",
  openGraph: {
    title: "VULMS AI Companion",
    description:
      "AI-powered LMS companion for VU students — deadline tracking, extension sync, and WhatsApp alerts.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "VULMS AI Companion",
    description:
      "AI-powered LMS companion for VU students — deadline tracking, extension sync, and WhatsApp alerts.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
