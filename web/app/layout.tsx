import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenConch — AI that remembers",
  description: "Persistent episodic memory for AI conversations. Pick up where you left off.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#09090b] text-[#fafafa] h-screen overflow-hidden noise">
        {children}
      </body>
    </html>
  );
}
