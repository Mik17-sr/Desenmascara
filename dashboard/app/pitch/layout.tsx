import type { Metadata } from "next";

const SITE = "https://desenmascara.onrender.com";

// The link preview in WhatsApp, Telegram or LinkedIn: a frame of the video with the people in it.
export const metadata: Metadata = {
  title: "Pitch · El día de Doña Rosa · Desenmascara",
  description: "Desenmascara en 3 minutos: el falso familiar, el falso asesor del banco y el cobro falso, y qué ganan las entidades. Con datos reales.",
  openGraph: {
    type: "video.other",
    title: "El día de Doña Rosa · Desenmascara",
    description: "Reenvía el mensaje. Desenmascara la estafa. El pitch en 3 minutos.",
    images: [`${SITE}/pitch/portada.jpg`],
    videos: [{ url: `${SITE}/pitch/desenmascara-pitch.mp4`, type: "video/mp4", width: 1920, height: 1080 }],
  },
  twitter: { card: "summary_large_image", images: [`${SITE}/pitch/portada.jpg`] },
};

export default function PitchLayout({ children }: { children: React.ReactNode }) {
  return children;
}
