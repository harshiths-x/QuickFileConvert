import type { Metadata } from "next";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "QuickFileConvert — Convert files quickly", template: "%s | QuickFileConvert" },
  description: "Convert common documents, PDFs, images, and spreadsheets quickly. No account required.",
  openGraph: { title: "QuickFileConvert", description: "Convert files quickly. No account required.", type: "website" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{ __html: `try{var t=localStorage.getItem('theme');document.documentElement.dataset.theme=t|| (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}catch(e){}` }} /></head><body><Header /><main>{children}</main><Footer /></body></html>;
}
