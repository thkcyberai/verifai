// API Configuration
export const API_URL = __DEV__ 
  ? 'http://localhost:8000/api/v1'  // Development (your local backend)
  : 'https://api.verifai.com/api/v1'; // Production (when you deploy)

// App Configuration
export const APP_NAME = 'VerifAI';
export const APP_VERSION = '1.0.0';

// Timeouts (in milliseconds)
export const API_TIMEOUT = 30000; // 30 seconds
export const POLLING_INTERVAL = 2000; // 2 seconds

// Limits
export const MAX_CLAIM_LENGTH = 2000;
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

// Verdict Colors
export const VERDICT_COLORS = {
  TRUE: '#10b981',      // Green
  FALSE: '#ef4444',     // Red
  MISLEADING: '#f59e0b', // Orange
  UNVERIFIED: '#6b7280', // Gray
  NEEDS_CONTEXT: '#3b82f6', // Blue
};

// Confidence Thresholds
export const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.8,
  MEDIUM: 0.5,
  LOW: 0.3,
};
