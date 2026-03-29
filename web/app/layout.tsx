import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenConch",
  description: "AI that remembers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="h-screen overflow-hidden" suppressHydrationWarning>{children}</body>
    </html>
  );
}
