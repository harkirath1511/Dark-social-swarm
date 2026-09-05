/**
 * Accurately formats UTC timestamps to the user's local browser timezone.
 * Handles SQLite strings ("YYYY-MM-DD HH:MM:SS"), ISO strings ("...Z" or "...T..."), and epoch timestamps.
 */
export function formatLocalTime(timestamp?: string | number): string {
  if (!timestamp) return 'Just now';
  try {
    let date: Date;
    if (typeof timestamp === 'number') {
      date = new Date(timestamp > 1e11 ? timestamp : timestamp * 1000);
    } else {
      let str = String(timestamp).trim();
      if (!str) return 'Just now';
      
      // If already a relative string like "18m ago"
      if (str.includes('ago') || str.toLowerCase() === 'just now') {
        return str;
      }
      
      // If it looks like a pure numeric string (epoch timestamp)
      if (/^\d{10}(\.\d+)?$/.test(str)) {
        date = new Date(parseFloat(str) * 1000);
      } else if (/^\d{13}$/.test(str)) {
        date = new Date(parseInt(str, 10));
      } else {
        // Convert SQLite format "YYYY-MM-DD HH:MM:SS" into ISO format
        if (str.includes(' ') && !str.includes('T')) {
          str = str.replace(' ', 'T');
        }
        // If string does not have timezone offset (+/-HH:MM or Z), force UTC interpretation by appending 'Z'
        if (!str.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(str)) {
          str = str + 'Z';
        }
        date = new Date(str);
      }
    }

    if (isNaN(date.getTime())) return 'Recent';

    // Format local time e.g. "8:48 AM"
    const timeStr = date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });

    // Calculate elapsed minutes
    const diffMs = Date.now() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins >= 0 && diffMins < 1) {
      return `Just now (${timeStr})`;
    }
    if (diffMins >= 1 && diffMins < 60) {
      return `${diffMins}m ago (${timeStr})`;
    }
    if (diffHours >= 1 && diffHours < 24) {
      return `${diffHours}h ago (${timeStr})`;
    }

    return timeStr;
  } catch (e) {
    return 'Recent';
  }
}

