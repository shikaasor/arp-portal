import type { Metadata, Viewport } from "next";
import { AuthProvider } from "@/components/AuthProvider";
import { Shell } from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
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

export const viewport: Viewport = { themeColor: "#164e3c", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
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
