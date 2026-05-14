import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Polaris design system fonts — Space Grotesk for UI, JetBrains Mono for code.
// Loaded as variable fonts and exposed as CSS vars (--font-sans / --font-mono)
// that globals.css picks up.
const sans = Space_Grotesk({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Polaris — AI Agent Firewall",
  description:
    "Auto-generate AI agent security policies from compliance docs. SOC 2 PDF to live guardrail in 60 seconds.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
