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

export const viewport: Viewport = { themeColor: "#ffffff" };

// Light like the guide unless the viewer chose dark (shell.tsx); set before the first paint so it does not flash.
const THEME_SCRIPT = `try{if(localStorage.getItem("desenmascara.tema")==="dark")document.documentElement.dataset.theme="dark"}catch(e){}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" data-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className={`${inter.variable} ${jetbrains.variable} antialiased`}>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
