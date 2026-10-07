import type {Metadata} from "next";
import "./globals.css";

export const metadata: Metadata = {title: "Duolingo · Learn Spanish", description: "A full-stack language learning assignment with lessons, a learning path, and daily progress."};
export default function RootLayout({children}: {children: React.ReactNode}) {
  return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html: `try { document.documentElement.dataset.theme = localStorage.getItem("duolingo.theme.v1") === "dark" ? "dark" : "light"; } catch { document.documentElement.dataset.theme = "light"; }`}}/></head><body>{children}</body></html>;
}
