import type { ReactNode, SVGProps } from "react";

// Line icons drawn inline (24×24, lucide style) to avoid another dependency.
function icon(paths: ReactNode) {
  return function Icon(props: SVGProps<SVGSVGElement>) {
    return (
      <svg viewBox="0 0 24 24" width={18} height={18} fill="none" stroke="currentColor" strokeWidth={1.8}
           strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
        {paths}
      </svg>
    );
  };
}

export const Activity = icon(<path d="M22 12h-4l-3 9L9 3l-3 9H2" />);
export const ShieldCheck = icon(<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="m9 12 2 2 4-4" /></>);
export const Database = icon(<><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5" /><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3" /></>);
export const Building = icon(<><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" /><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" /><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2" /><path d="M10 6h4M10 10h4M10 14h4M10 18h4" /></>);
export const Menu = icon(<path d="M4 6h16M4 12h16M4 18h16" />);
export const Close = icon(<path d="M18 6 6 18M6 6l12 12" />);
export const AlertTriangle = icon(<><path d="m21.7 18-8-14a2 2 0 0 0-3.5 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z" /><path d="M12 9v4M12 17h.01" /></>);
export const Phone = icon(<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z" />);
export const CheckCircle = icon(<><path d="M22 11.1V12a10 10 0 1 1-5.9-9.1" /><path d="m9 11 3 3L22 4" /></>);
export const Megaphone = icon(<><path d="m3 11 18-5v12L3 14v-3z" /><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6" /></>);
export const Gauge = icon(<><path d="m12 14 4-4" /><path d="M3.3 19a10 10 0 1 1 17.4 0" /></>);
export const Search = icon(<><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></>);
export const Key = icon(<><circle cx="7.5" cy="15.5" r="5.5" /><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3" /></>);
export const Copy = icon(<><rect x="8" y="8" width="14" height="14" rx="2" /><path d="M4 16a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2" /></>);
export const TrendUp = icon(<><path d="M22 7 13.5 15.5l-5-5L2 17" /><path d="M16 7h6v6" /></>);
export const TrendDown = icon(<><path d="M22 17 13.5 8.5l-5 5L2 7" /><path d="M16 17h6v-6" /></>);
export const Message = icon(<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />);
export const Mic = icon(<><rect x="9" y="2" width="6" height="13" rx="3" /><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3" /></>);
export const ImageIcon = icon(<><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21" /></>);
export const Users = icon(<><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></>);
export const Logout = icon(<><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5M21 12H9" /></>);
export const Server = icon(<><rect x="2" y="2" width="20" height="8" rx="2" /><rect x="2" y="14" width="20" height="8" rx="2" /><path d="M6 6h.01M6 18h.01" /></>);
export const Cpu = icon(<><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2" /></>);
export const Radio = icon(<><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9M7.8 16.2a6 6 0 0 1 0-8.5" /><circle cx="12" cy="12" r="2" /><path d="M16.2 7.8a6 6 0 0 1 0 8.5M19.1 4.9C23 8.8 23 15.1 19.1 19" /></>);
export const Link2 = icon(<><path d="M9 17H7A5 5 0 0 1 7 7h2M15 7h2a5 5 0 1 1 0 10h-2" /><path d="M8 12h8" /></>);
