/**
 * Utility functions for validating Link href values
 */

/**
 * Validates if a value is a valid href for Next.js Link component
 * @param href - The href value to validate
 * @returns boolean indicating if the href is valid
 */
export function isValidHref(href: any): href is string {
  if (href === null || href === undefined) {
    return false;
  }
  
  if (typeof href !== 'string') {
    return false;
  }
  
  if (href.trim() === '') {
    return false;
  }
  
  return true;
}

/**
 * Sanitizes an href value for use with Next.js Link component
 * @param href - The href value to sanitize
 * @param fallback - Fallback href if the original is invalid
 * @returns A valid href string
 */
export function sanitizeHref(href: any, fallback: string = '/'): string {
  if (isValidHref(href)) {
    return href.trim();
  }
  
  console.warn('Invalid href provided to Link component:', href, 'Using fallback:', fallback);
  return fallback;
}

/**
 * Creates a safe chat href
 * @param chatId - The chat ID
 * @returns A valid chat href
 */
export function createSafeChatHref(chatId: any): string {
  if (!isValidHref(chatId)) {
    console.warn('Invalid chatId for chat link:', chatId);
    return '/chat';
  }
  
  return `/chat/${chatId.trim()}`;
}

/**
 * Creates a safe external link href
 * @param url - The external URL
 * @returns A valid external href or null if invalid
 */
export function createSafeExternalHref(url: any): string | null {
  if (!isValidHref(url)) {
    return null;
  }
  
  const trimmedUrl = url.trim();
  
  // Basic URL validation
  try {
    new URL(trimmedUrl);
    return trimmedUrl;
  } catch {
    // If it's not a valid URL, check if it's a relative path
    if (trimmedUrl.startsWith('/') || trimmedUrl.startsWith('#')) {
      return trimmedUrl;
    }
    
    console.warn('Invalid URL for external link:', url);
    return null;
  }
}
