import Link from "next/link";
import { IBM_Plex_Mono, Inter, Spectral } from "next/font/google";
import "./globals.css";

const display = Spectral({ weight: ["300", "400", "500"], subsets: ["latin"], variable: "--font-display" });
const body = Inter({ subsets: ["latin"], variable: "--font-body" });
const mono = IBM_Plex_Mono({ weight: ["400", "600"], subsets: ["latin"], variable: "--font-mono" });

export const metadata = {
  title: "CAP — Carbon-transition Asset Pricing",
  description:
    "The anatomy of the transition-risk premium for Korean and Japanese heavy industry — decomposed into four hedgeable drivers.",
};

const NAV = [
  ["/", "Overview"],
  ["/wedge", "Wedge"],
  ["/sectors", "Sectors"],
  ["/theory", "Method"],
  ["/ledger", "Ledger"],
  ["/data", "Data"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body>
        <header className="nav">
          <div className="nav__inner">
            <a href="https://planit.institute" className="nav__logo" aria-label="PLANiT Institute">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/planit-logo.png" alt="PLANiT Institute" style={{ height: 15, display: "block" }} />
            </a>
            <Link href="/" className="nav__title" style={{ textDecoration: "none" }}>
              CAP
            </Link>
            <nav className="nav__links">
              {NAV.map(([href, label]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        {children}
        <footer className="footer">
          <div className="footer__inner">
            <div>
              CAP — Carbon-transition Asset Pricing · <a href="https://planit.institute">PLANiT Institute</a>
              <br />
              Every number on this site is a computed artifact of the open model pipeline.
            </div>
            <div className="mono">
              <Link href="/ledger">proven vs conditional ledger</Link> · <Link href="/data">data provenance</Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
