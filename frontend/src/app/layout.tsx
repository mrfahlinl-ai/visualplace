import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AI Visual Place Finder — Find Where a Photo Was Taken",
    template: "%s — VisualPlace",
  },
  description:
    "Upload an image and let AI analyze landmarks, signs, architecture, geography, and other visual clues to identify the most likely location.",
  applicationName: "VisualPlace",
  keywords: [
    "visual geolocation",
    "photo location finder",
    "where was this photo taken",
    "AI image location",
    "landmark identification",
  ],
  openGraph: {
    title: "AI Visual Place Finder — Find Where a Photo Was Taken",
    description:
      "Evidence-based AI geolocation: landmarks, signs, architecture and geography — with a transparent explanation of why.",
    type: "website",
    siteName: "VisualPlace",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Visual Place Finder",
    description:
      "Upload a photo. See the most likely location — and the evidence behind it.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbfbfd" },
    { media: "(prefers-color-scheme: dark)", color: "#07080d" },
  ],
};

// Set the theme class before paint to avoid a flash of the wrong theme.
const themeInit = `(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.classList.toggle('dark',d);}catch(e){}})();`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
