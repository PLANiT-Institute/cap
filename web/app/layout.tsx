import Link from "next/link";
import { IBM_Plex_Mono, Inter, Spectral } from "next/font/google";
import "./globals.css";

const display = Spectral({ weight: ["300", "400", "500"], subsets: ["latin"], variable: "--font-display" });
const body = Inter({ subsets: ["latin"], variable: "--font-body" });
const mono = IBM_Plex_Mono({ weight: ["400", "600"], subsets: ["latin"], variable: "--font-mono" });

export const metadata = {
  title: "CAP — Transition-risk underwriter",
  description:
    "Translate industrial technology choices into financial risk anatomy and test which contracts reduce the conditional transition-risk charge.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body className="dark-app">
        <header className="nav">
          <div className="nav__inner">
            <a href="https://planit.institute" className="nav__logo" aria-label="PLANiT Institute">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/planit-logo.png" alt="PLANiT Institute" style={{ height: 15, display: "block" }} />
            </a>
            <Link href="/" className="nav__title" style={{ textDecoration: "none" }}>
              CAP
            </Link>
            <span className="nav__tag">transition-risk underwriter</span>
            <nav className="nav__links">
              <Link href="/">Underwrite</Link>
              <Link href="/pilots">Pilots</Link>
              <Link href="/method">Method</Link>
              <a href="https://github.com/PLANiT-Institute/cap">GitHub</a>
            </nav>
          </div>
        </header>
        {children}
        <footer className="footer">
          <div className="footer__inner">
            <div>
              CAP · <a href="https://planit.institute">PLANiT Institute</a> — every number is a
              computed artifact of the open pipeline.
            </div>
            <div className="mono">API + MCP access: coming — the model core is already callable.</div>
          </div>
        </footer>
      </body>
    </html>
  );
}
