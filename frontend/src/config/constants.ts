/**
 * Application configuration constants
 */

/**
 * Application version
 */
export const APP_VERSION = "1.0.0";

/**
 * Application name
 */
export const APP_NAME = "Kino";

/**
 * Backend API base URL (HTTP)
 */
export const API_BASE_URL = "http://localhost:8000";

/**
 * Backend WebSocket URL
 */
export const WS_URL = "ws://localhost:8000/ws";

/**
 * WebSocket reconnection delay in milliseconds
 */
export const WS_RECONNECT_DELAY = 3000; // 3 seconds

/**
 * Get frame image URL by frame path
 */
export const getFrameImageUrl = (framePath: string): string => {
  // Frame path is absolute, so we need to construct URL differently
  const filename = framePath.split("/").pop();
  return `${API_BASE_URL}/data/frames/${filename}`;
};
