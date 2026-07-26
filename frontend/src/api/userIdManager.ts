const USER_ID_KEY = 'user_id';
const VERIFICATION_CACHE_KEY = 'user_id_verification_time';
const VERIFICATION_CACHE_TTL = 30 * 60 * 1000; // 30 minutes in milliseconds
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class UserIDManager {
  /**
   * Get existing user ID from localStorage or generate a new one
   * Verifies on first load and then caches verification result
   */
  static async getOrCreateUserId(): Promise<string> {
    const existing = localStorage.getItem(USER_ID_KEY);
    if (existing) {
      // Check if we should verify based on cache TTL
      const lastVerification = localStorage.getItem(VERIFICATION_CACHE_KEY);
      const now = Date.now();
      
      if (lastVerification && (now - parseInt(lastVerification)) < VERIFICATION_CACHE_TTL) {
        // Cache is still valid, return without verification
        return existing;
      }
      
      // Cache expired or no cache, verify the token
      const isValid = await this.verifyUserIdOnServer(existing);
      if (isValid) {
        localStorage.setItem(VERIFICATION_CACHE_KEY, now.toString());
        return existing;
      }
      
      // Token expired or invalid, remove it and generate new one
      localStorage.removeItem(USER_ID_KEY);
      localStorage.removeItem(VERIFICATION_CACHE_KEY);
    }

    // Generate new user ID
    return this.generateNewUserId();
  }

  /**
   * Generate a new user ID from the server
   */
  static async generateNewUserId(): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/generate-user-id`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to generate user ID: ${response.statusText}`);
      }

      const data = await response.json();
      const userID = data.user_id;

      // Store in localStorage and cache verification timestamp
      localStorage.setItem(USER_ID_KEY, userID);
      localStorage.setItem(VERIFICATION_CACHE_KEY, Date.now().toString());
      return userID;
    } catch (error) {
      console.error('Error generating user ID:', error);
      throw error;
    }
  }

  /**
   * Verify user ID on server (uses cache to avoid excessive API calls)
   */
  static async verifyUserIdOnServer(userID: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/verify-user-id`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userID }),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      return data.valid === true;
    } catch (error) {
      console.error('Error verifying user ID:', error);
      return false;
    }
  }

  /**
   * Get current user ID (from localStorage only, no generation)
   */
  static getCurrentUserId(): string | null {
    return localStorage.getItem(USER_ID_KEY);
  }

  /**
   * Clear user ID from localStorage
   */
  static clearUserId(): void {
    localStorage.removeItem(USER_ID_KEY);
    localStorage.removeItem(VERIFICATION_CACHE_KEY);
  }

  /**
   * Extract UUID from signed token (for debugging/display)
   * Format: {uuid}.{timestamp}.{signature}
   */
  static extractUuidFromToken(token: string): string | null {
    const parts = token.split('.');
    return parts.length === 3 ? parts[0] : null;
  }
}

