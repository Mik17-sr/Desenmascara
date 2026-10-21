import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import { Nav } from "@/components/nav";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Desenmascara · Dashboard",
  description: "Radar de campañas de estafa, verificación de mensajes, Banco de números y Panel de la entidad.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${inter.variable} ${jetbrains.variable} antialiased`}>
        <Nav />
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
