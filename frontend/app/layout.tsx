import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "./context/AuthContext";
import { Navbar } from "../components/Navbar";

import { CosmicBackground } from "../components/CosmicBackground";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Jarvis - AI Assistant",
  description: "Advanced AI Assistant with Memory",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossOrigin="anonymous" />
      </head>
      <body className={`${inter.className} bg-background text-foreground min-h-screen overflow-hidden`}>
        <AuthProvider>
          <CosmicBackground />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
