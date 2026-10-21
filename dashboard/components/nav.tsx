"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/ui";

const VIEWS = [
  { href: "/", label: "Radar" },
  { href: "/verificar", label: "Verificar un mensaje" },
  { href: "/banco", label: "Banco de números" },
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold">
          <Logo />
          <span>
            Desen<span className="text-brand">mascara</span>
          </span>
        </Link>
        <nav className="order-3 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto">
          {VIEWS.map((view) => {
            const active = view.href === "/" ? path === "/" : path.startsWith(view.href);
            return (
              <Link
                key={view.href}
                href={view.href}
                aria-current={active ? "page" : undefined}
                className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ${active ? "bg-mint text-brand-ink" : "text-muted hover:text-ink"}`}
              >
                {view.label}
              </Link>
            );
          })}
        </nav>
        <Link
          href="/entidad"
          className={`ml-auto whitespace-nowrap text-sm font-medium ${path.startsWith("/entidad") ? "text-brand-ink" : "text-muted hover:text-ink"}`}
        >
          Acceso para entidades →
        </Link>
      </div>
    </header>
  );
}
