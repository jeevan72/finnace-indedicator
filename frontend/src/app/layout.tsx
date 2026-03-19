import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Financial Intelligence Terminal",
  description: "India-focused commodity, equity, and macro intelligence dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 antialiased min-h-screen">
        {/* Top Nav */}
        <nav className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📈</span>
                <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  Financial Intelligence Terminal
                </h1>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-gray-500">
                  Powered by FastAPI + Next.js
                </span>
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" title="Live" />
              </div>
            </div>
          </div>
        </nav>
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
