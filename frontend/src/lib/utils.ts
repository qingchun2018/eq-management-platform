import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** 合并并去重 Tailwind class 名（shadcn ui 通用工具） */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
