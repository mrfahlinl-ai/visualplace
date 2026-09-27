import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names with correct precedence. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
