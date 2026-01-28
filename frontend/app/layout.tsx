import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "./context/AuthContext";
import { Navbar } from "../components/Navbar";

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
      <body className={`${inter.className} bg-slate-950 text-white min-h-screen overflow-x-hidden`}>
        <AuthProvider>
          <Navbar />
          <div className="pt-20 min-h-screen">
            {children}
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
