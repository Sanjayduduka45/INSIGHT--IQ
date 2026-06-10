/**
 * InsightIQ — Global Value Formatting Layer
 * Implements executive-grade number, percentage, and currency formatting.
 */

export function getDetectedLocaleAndCurrency() {
  let lang = typeof window !== 'undefined' ? localStorage.getItem('language') : null;
  if (!lang && typeof navigator !== 'undefined') {
    lang = navigator.language;
  }
  const isIndianLocale = (lang && lang.includes('IN')) || (
    typeof window !== 'undefined' && Intl.DateTimeFormat().resolvedOptions().timeZone && 
    ['Asia/Kolkata', 'Asia/Calcutta'].includes(Intl.DateTimeFormat().resolvedOptions().timeZone)
  );
  return {
    locale: isIndianLocale ? 'en-IN' : 'en-US',
    currency: isIndianLocale ? 'INR' : 'USD'
  };
}

/**
 * Formats a numeric value to a compact currency format.
 * Convert: 40613568 -> To: ₹4.06 Crores (en-IN) or ₹40.61M (en-US)
 */
export function formatCurrency(val: number, currency?: string): string {
  if (typeof val !== 'number' || isNaN(val)) return '₹0.00';
  
  const detected = getDetectedLocaleAndCurrency();
  const curr = currency || detected.currency;
  const useIndianNotation = detected.locale === 'en-IN';
  const sign = val < 0 ? '-' : '';
  const absVal = Math.abs(val);

  if (curr === 'INR') {
    if (useIndianNotation) {
      if (absVal >= 10000000) {
        return `${sign}₹${(absVal / 10000000).toFixed(2)} Crores`;
      } else if (absVal >= 100000) {
        return `${sign}₹${(absVal / 100000).toFixed(2)} Lakhs`;
      } else if (absVal >= 1000) {
        return `${sign}₹${(absVal / 1000).toFixed(2)} K`;
      } else {
        return `${sign}₹${absVal.toFixed(2)}`;
      }
    } else {
      if (absVal >= 1000000) {
        return `${sign}₹${(absVal / 1000000).toFixed(2)}M`;
      } else if (absVal >= 1000) {
        return `${sign}₹${(absVal / 1000).toFixed(2)}K`;
      } else {
        return `${sign}₹${absVal.toFixed(2)}`;
      }
    }
  }

  // For USD or other currencies
  if (useIndianNotation) {
    if (absVal >= 10000000) {
      return `${sign}$${(absVal / 10000000).toFixed(2)} Crores`;
    } else if (absVal >= 100000) {
      return `${sign}$${(absVal / 100000).toFixed(2)} Lakhs`;
    } else if (absVal >= 1000) {
      return `${sign}$${(absVal / 1000).toFixed(2)} K`;
    } else {
      return `${sign}$${absVal.toFixed(2)}`;
    }
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: curr,
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 2
  }).format(val);
}

/**
 * Formats a number to compact form.
 * E.g., 40613568 -> 40.6M (or 4.06 Crores in INR context)
 */
export function formatCompactNumber(
  val: number,
  options?: { isCurrency?: boolean; currency?: string }
): string {
  if (typeof val !== 'number' || isNaN(val)) return '0';
  
  const detected = getDetectedLocaleAndCurrency();
  const curr = options?.currency || detected.currency;

  if (options?.isCurrency) {
    return formatCurrency(val, curr);
  }

  const useIndianNotation = detected.locale === 'en-IN';
  const sign = val < 0 ? '-' : '';
  const absVal = Math.abs(val);

  if (useIndianNotation) {
    if (absVal >= 10000000) {
      return `${sign}${(absVal / 10000000).toFixed(2)} Crores`;
    } else if (absVal >= 100000) {
      return `${sign}${(absVal / 100000).toFixed(2)} Lakhs`;
    } else if (absVal >= 1000) {
      return `${sign}${(absVal / 1000).toFixed(2)} K`;
    } else {
      return `${sign}${absVal.toFixed(2)}`;
    }
  }

  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 2
  }).format(val);
}

/**
 * Formats percentage value.
 * Convert: 0.0041 -> 0.41%
 */
export function formatPercent(val: number, isFraction?: boolean): string {
  if (typeof val !== 'number' || isNaN(val)) return '0.00%';
  
  const useFraction = isFraction ?? (Math.abs(val) <= 1.0);
  const num = useFraction ? val * 100.0 : val;
  return `${num.toFixed(2)}%`;
}
