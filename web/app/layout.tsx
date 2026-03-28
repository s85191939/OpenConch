import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenConch",
  description: "AI that remembers. Powered by episodic memory.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0d0d0d] text-[#ececec] h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}
