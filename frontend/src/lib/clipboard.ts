/**
 * Copy text to clipboard with fallback support for older browsers
 * and non-secure contexts.
 * 
 * @param text - The text to copy to clipboard
 * @returns Promise<boolean> - True if copy was successful, false otherwise
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // Guard against non-browser environments (tests, SSR, etc.)
  if (
    typeof window === "undefined" ||
    typeof navigator === "undefined" ||
    typeof document === "undefined"
  ) {
    return false;
  }

  // Try modern Clipboard API first (requires secure context)
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fall through to fallback method
    }
  }

  // Fallback using execCommand for older browsers or non-secure contexts
  return fallbackCopyToClipboard(text);
}

/**
 * Fallback copy method using the deprecated but widely supported execCommand
 * 
 * @param text - The text to copy
 * @returns boolean - True if copy was successful, false otherwise
 */
function fallbackCopyToClipboard(text: string): boolean {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  
  // Prevent scrolling to bottom of page and keep element invisible
  textarea.style.cssText = "position:fixed;left:-9999px;top:-9999px;opacity:0";
  
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();

  try {
    const successful = document.execCommand("copy");
    return successful;
  } catch {
    return false;
  } finally {
    document.body.removeChild(textarea);
  }
}
