import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Plus_Jakarta_Sans } from "next/font/google";
import { AuthProvider } from "@/components/AuthProvider";
import { Shell } from "@/components/Shell";
import { config } from "@/lib/config";
import "./globals.css";

const display = Bricolage_Grotesque({ subsets: ["latin"], weight: ["600", "700", "800"], variable: "--font-display" });
const body = Plus_Jakarta_Sans({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-body" });

export const metadata: Metadata = {
  metadataBase: new URL(config.siteUrl),
  title: { default: "ARP | Empowerment Portal", template: "%s | ARP Empowerment Portal" },
  description:
    "Arewa Revival Project empowerment portal: apply for the proposed 5,000 Youth Global Entrepreneurship Initiative across the 19 Northern States.",
  icons: { icon: "/assets/arp-logo.jpeg" },
  openGraph: {
    title: "Arewa Revival Project | Empowerment Portal",
    description: "Connecting Northern youth to opportunities for growth.",
    images: ["/assets/arp-logo.jpeg"],
    type: "website",
  },
};

export const viewport: Viewport = { themeColor: "#0b3d2c", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>
        <a className="skip" href="#main">
          Skip to content
        </a>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
      </body>
    </html>
  );
}
