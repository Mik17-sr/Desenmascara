"use client";

import { useEffect, useRef, useState } from "react";

/** Animates a number from its previous value to the new one, so live changes are noticed. */
export function useCountUp(target: number, durationMs = 700): number {
  const [value, setValue] = useState(target);
  const from = useRef(target);

  useEffect(() => {
    const start = from.current;
    if (start === target || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      from.current = target;
      setValue(target);
      return;
    }
    const began = performance.now();
    let frame = 0;
    const step = (now: number) => {
      const t = Math.min(1, (now - began) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(start + (target - start) * eased);
      if (t < 1) frame = requestAnimationFrame(step);
      else from.current = target;
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [target, durationMs]);

  return value;
}
