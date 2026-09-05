/**
 * Render backend ISO timestamps in the viewer's local timezone.
 *
 * @param {string | number | Date} value
 * @param {string | string[]} [locale]
 * @returns {string}
 */
export function formatLocalTime(value, locale) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return 'Recent';

  return new Intl.DateTimeFormat(locale, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}
