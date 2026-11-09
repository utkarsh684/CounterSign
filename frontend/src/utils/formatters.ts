/**
 * Currency and date formatting utilities.
 */

export function formatMinorUnits(minorUnits: number, currency: string = "USD"): string {
  const isZeroDecimal = ["JPY", "KRW"].includes(currency.toUpperCase());
  const val = isZeroDecimal ? minorUnits : minorUnits / 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
    minimumFractionDigits: isZeroDecimal ? 0 : 2,
    maximumFractionDigits: isZeroDecimal ? 0 : 2,
  }).format(val);
}

export function formatDate(isoString?: string): string {
  if (!isoString) return "N/A";
  const date = new Date(isoString);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function truncateHash(hash: string, length: number = 10): string {
  if (!hash || hash.length <= length * 2) return hash;
  return `${hash.slice(0, length)}...${hash.slice(-length)}`;
}
