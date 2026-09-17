/** Turn a snake_case identifier into readable title case: "glass_shatter" -> "Glass Shatter". */
export function readable(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/** Format a 0–1 score as a percentage with one decimal place: 0.8547 -> "85.5%". */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
