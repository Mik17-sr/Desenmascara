import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import { Shell } from "@/components/shell";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Desenmascara · Plataforma antifraude",
  description: "Radar de campañas de estafa, verificación de mensajes, Banco de números y Panel de la entidad.",
};

export const viewport: Viewport = {
  themeColor: [{ media: "(prefers-color-scheme: light)", color: "#ffffff" }, { media: "(prefers-color-scheme: dark)", color: "#0b100f" }],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${inter.variable} ${jetbrains.variable} antialiased`}>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
