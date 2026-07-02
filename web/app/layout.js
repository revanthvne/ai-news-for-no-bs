import "./globals.css";

export const metadata = {
  title: "NO BS — Should You Buy This?",
  description: "Daily AI, chips, robotics, eVTOL & drone news with honest buy/skip verdicts.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <header>
            <div className="brand">
              NO BS <span style={{ color: "var(--accent)" }}>·</span>{" "}
              <span className="sub">Should You Buy This?</span>
            </div>
            <div className="tagline">
              The hype, the reality, and whether your money is worth it — daily.
            </div>
          </header>
          {children}
          <div className="footer">
            Auto-generated pipeline · facts link to primary sources · not financial advice.
          </div>
        </div>
      </body>
    </html>
  );
}
