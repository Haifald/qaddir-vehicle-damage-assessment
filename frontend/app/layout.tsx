import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Qaddir | Vehicle Damage Assessment",
  description: "AI-assisted preliminary vehicle damage assessment for qualified human review.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
