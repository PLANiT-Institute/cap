import Link from "next/link";
import tokens from "../tokens.json";

export const metadata = {
  title: "CAP — Carbon-transition Asset Pricing",
  description: "한·일 철강 transition-risk premium의 anatomy",
};

const NAV = [
  ["/", "Anatomy"],
  ["/wedge", "Wedge"],
  ["/theory", "Theory"],
  ["/ledger", "Ledger"],
  ["/data", "Data"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body
        style={{
          margin: 0,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif",
          backgroundColor: tokens.palette.paper,
          color: tokens.palette.ink,
        }}
      >
        <header
          style={{
            backgroundColor: tokens.palette.navy,
            color: "white",
            padding: "12px 24px",
            display: "flex",
            alignItems: "baseline",
            gap: 24,
          }}
        >
          <a
            href="https://planit.institute"
            style={{
              backgroundColor: "white",
              borderRadius: 4,
              padding: "3px 8px",
              display: "flex",
              alignItems: "center",
              alignSelf: "center",
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/planit-logo.png" alt="PLANiT Institute" style={{ height: 16, display: "block" }} />
          </a>
          <strong style={{ fontSize: 18 }}>CAP</strong>
          <span style={{ fontSize: 12, opacity: 0.8 }}>
            Carbon-transition Asset Pricing — 한·일 철강 anatomy
          </span>
          <nav style={{ marginLeft: "auto", display: "flex", gap: 16 }}>
            {NAV.map(([href, label]) => (
              <Link key={href} href={href} style={{ color: "white", fontSize: 14, textDecoration: "none" }}>
                {label}
              </Link>
            ))}
          </nav>
        </header>
        <main style={{ maxWidth: 960, margin: "0 auto", padding: "24px 16px 64px" }}>{children}</main>
      </body>
    </html>
  );
}
