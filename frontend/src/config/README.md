# Configuration Constants

This directory contains centralized configuration constants used throughout the application.

## constants.ts

Centralized configuration file for all application-wide constants.

### Available Constants

#### Application Info
- `APP_NAME` - Application name ("Kino")
- `APP_VERSION` - Application version (synced with package.json)

#### Backend URLs
- `API_BASE_URL` - Backend HTTP API base URL
- `WS_URL` - Backend WebSocket URL for real-time updates

#### WebSocket Configuration
- `WS_RECONNECT_DELAY` - WebSocket reconnection delay in milliseconds

#### Helper Functions
- `getFrameImageUrl(framePath: string)` - Constructs frame image URL from frame path

## Usage Examples

### Importing Constants

```typescript
import { API_BASE_URL, APP_NAME, APP_VERSION } from '../config/constants';
```

### Using in Components

```typescript
// Display app name
<h1>{APP_NAME}</h1>

// Display version
<p>Version {APP_VERSION}</p>

// Make API call
fetch(`${API_BASE_URL}/api/v1/projects`)
```

### Using Helper Functions

```typescript
import { getFrameImageUrl } from '../config/constants';

const frameUrl = getFrameImageUrl(frame.path);
```

## Why Centralized Constants?

1. **Single Source of Truth** - Change once, apply everywhere
2. **Easy Configuration** - All settings in one place
3. **Type Safety** - TypeScript ensures correct usage
4. **Maintainability** - No magic strings scattered across codebase
5. **Environment Switching** - Easy to adapt for different environments (dev, staging, prod)

## Future Improvements

Consider moving to environment variables for production:
- Use `.env` files for different environments
- Import via `import.meta.env.VITE_*` in Vite
- Keep constants.ts as fallback/defaults

