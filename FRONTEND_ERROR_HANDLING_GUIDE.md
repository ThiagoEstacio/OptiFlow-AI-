# Frontend Error Handling - Developer Guide

## Quick Reference

### Using the Enhanced API Client

The API client now handles errors automatically. No changes needed to existing code!

```typescript
// Existing code works as-is
try {
  const data = await apiClient.getSites();
  // Success
} catch (error) {
  // This only fires after automatic retries are exhausted
  showErrorToast(error); // Automatic user-friendly message
}
```

**What happens automatically:**
1. Request sent with 30-second timeout
2. If network/server error: Retry up to 3 times with exponential backoff
3. If still fails: Error thrown to your catch block

### Showing Toast Notifications

```typescript
import {
  showSuccessToast,
  showErrorToast,
  showLoadingToast,
  dismissToast
} from '../utils/toast';

// Success message
showSuccessToast('Operation completed!');

// Error with automatic user-friendly message
showErrorToast(error);

// Error with custom message
showErrorToast(error, 'Failed to save settings');

// Loading state
const toastId = showLoadingToast('Saving...');
// Later...
dismissToast(toastId);
showSuccessToast('Saved!');

// API error with context
import { handleApiError } from '../utils/toast';
try {
  await apiClient.updateDevice(id, data);
} catch (error) {
  handleApiError(error, 'Update device failed');
}
```

### Available Toast Functions

```typescript
// Basic notifications
showSuccessToast(message: string)
showErrorToast(error: any, customMessage?: string)
showInfoToast(message: string)
showWarningToast(message: string)

// Loading states
const id = showLoadingToast(message: string)
dismissToast(toastId: string)
updateToast(toastId: string, type: 'success'|'error'|'loading', message: string)

// Specific errors
showTimeoutToast()
showNetworkErrorToast()
showServerErrorToast()

// Helper
handleApiError(error: any, context?: string)
```

### Getting User-Friendly Error Messages

```typescript
import { getErrorMessage } from '../api/client';

try {
  await someOperation();
} catch (error) {
  const message = getErrorMessage(error);
  // message = "Unable to connect to server..." (not "ERR_NETWORK")
  console.log(message);
}
```

### Using Error Boundary in Components

The global error boundary is already set up. For component-specific boundaries:

```typescript
import { ErrorBoundary } from '../components/ErrorBoundary';

function MyPage() {
  return (
    <ErrorBoundary>
      <MyComplexComponent />
    </ErrorBoundary>
  );
}
```

Custom fallback UI:

```typescript
<ErrorBoundary
  fallback={
    <div>Custom error UI here</div>
  }
>
  <MyComponent />
</ErrorBoundary>
```

### Handling Login Errors

The login page automatically handles timeout and network errors. If building a custom login:

```typescript
import { useAppSelector } from '../store';

function CustomLogin() {
  const { error, isTimeout, isNetworkError } = useAppSelector(
    (state) => state.auth
  );

  if (isTimeout) {
    // Show timeout-specific message
  }

  if (isNetworkError) {
    // Show network-specific message
  }
}
```

## Common Patterns

### Pattern 1: Simple API Call

```typescript
const handleSave = async () => {
  try {
    await apiClient.updateSite(siteId, data);
    showSuccessToast('Site updated successfully!');
  } catch (error) {
    showErrorToast(error); // Automatic user-friendly message
  }
};
```

### Pattern 2: Loading State with Error Handling

```typescript
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  const toastId = showLoadingToast('Saving changes...');

  try {
    await apiClient.updateDevice(deviceId, formData);
    updateToast(toastId, 'success', 'Changes saved!');
  } catch (error) {
    dismissToast(toastId);
    showErrorToast(error);
  } finally {
    setLoading(false);
  }
};
```

### Pattern 3: Multiple Operations with Context

```typescript
const handleBulkUpdate = async () => {
  try {
    await apiClient.updateDevice(id1, data1);
    await apiClient.updateDevice(id2, data2);
    showSuccessToast('All devices updated!');
  } catch (error) {
    handleApiError(error, 'Bulk update failed');
    // Shows: "Bulk update failed: Server is temporarily unavailable..."
  }
};
```

### Pattern 4: Custom Error Handling

```typescript
const handleDelete = async () => {
  try {
    await apiClient.deleteDevice(deviceId);
    showSuccessToast('Device deleted');
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 403) {
        showErrorToast(null, 'You cannot delete this device because it has active tags.');
        return;
      }
    }
    // Default error handling
    showErrorToast(error);
  }
};
```

## Error Types and Messages

| Error Type | User Sees | Developer Action |
|------------|-----------|------------------|
| Network Error | "Unable to connect to server. Please check your internet connection." | None - auto-retry |
| Timeout | "Request timed out. Please check your connection and try again." | None - auto-retry |
| 401 Unauthorized | "Your session has expired. Please log in again." | Auto-redirect to login |
| 403 Forbidden | "You do not have permission to perform this action." | Check user permissions |
| 404 Not Found | "The requested resource was not found." | Check resource ID |
| 500-504 Server | "Server is temporarily unavailable. Please try again in a moment." | None - auto-retry |
| 429 Rate Limit | "Too many requests. Please wait a moment and try again." | None - auto-retry |

## Configuration

### Adjusting Timeout and Retry Settings

Edit `/frontend/src/api/client.ts`:

```typescript
// Current values
const API_TIMEOUT = 30000;           // 30 seconds
const MAX_RETRIES = 3;               // 3 retry attempts
const RETRY_DELAYS = [1000, 2000, 4000]; // 1s, 2s, 4s delays

// To make more aggressive (faster failures):
const API_TIMEOUT = 15000;           // 15 seconds
const MAX_RETRIES = 2;               // 2 retries
const RETRY_DELAYS = [500, 1000];    // 0.5s, 1s

// To make more patient (longer wait):
const API_TIMEOUT = 60000;           // 60 seconds
const MAX_RETRIES = 5;               // 5 retries
const RETRY_DELAYS = [1000, 2000, 4000, 8000, 16000]; // Exponential
```

### Customizing Toast Duration

Edit `/frontend/src/utils/toast.ts` or pass options:

```typescript
toast.success('Message', {
  duration: 5000, // 5 seconds
  position: 'top-center',
});
```

## Best Practices

### DO:
- Use `showErrorToast(error)` for automatic user-friendly messages
- Let the API client handle retries automatically
- Show loading states for long operations
- Provide context in error messages: `handleApiError(error, 'Save failed')`
- Clear errors when user starts correcting them

### DON'T:
- Display raw error objects to users
- Show technical error codes in UI
- Retry manually (API client does it)
- Use `alert()` for errors (use toast)
- Ignore errors silently

## Testing Error Handling

### Simulate Network Timeout

```typescript
// In your component test
jest.mock('../api/client', () => ({
  apiClient: {
    getSites: jest.fn().mockRejectedValue(
      new Error('ECONNABORTED')
    )
  }
}));
```

### Simulate Server Error

```typescript
jest.mock('../api/client', () => ({
  apiClient: {
    updateDevice: jest.fn().mockRejectedValue({
      response: { status: 500, data: { message: 'Internal error' } }
    })
  }
}));
```

### Test Error Boundary

```typescript
// Trigger error in component
const ThrowError = () => {
  throw new Error('Test error');
};

render(
  <ErrorBoundary>
    <ThrowError />
  </ErrorBoundary>
);

expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
```

## Troubleshooting

### Issue: Errors not showing toast
**Solution:** Make sure `<Toaster />` is mounted in App.tsx (already done).

### Issue: Retries not happening
**Check:** Look for console warnings showing retry attempts. Retries only happen for network/server errors, not validation errors.

### Issue: Login stuck on "Signing in..."
**This is fixed!** The new implementation:
1. Times out after 30 seconds
2. Retries automatically
3. Shows clear error message
4. Provides retry option

### Issue: Want to disable retry for specific request
```typescript
// Add custom axios config
const response = await apiClient.client.get('/api/endpoint', {
  // This will prevent retries for this specific call
  validateStatus: (status) => status < 500
});
```

## Migration Guide

### Updating Existing Error Handling

**Before:**
```typescript
try {
  await apiClient.getSites();
} catch (error) {
  toast.error('Failed to load sites');
}
```

**After:**
```typescript
try {
  await apiClient.getSites();
} catch (error) {
  showErrorToast(error); // Automatic user-friendly message
  // OR
  handleApiError(error, 'Failed to load sites');
}
```

### Updating Toast Calls

**Before:**
```typescript
import { showToast } from '../utils/toast';
showToast.error('Error message');
```

**After:**
```typescript
import { showErrorToast } from '../utils/toast';
showErrorToast(null, 'Error message');
// OR better - let it handle the error:
showErrorToast(error); // Automatic message from error
```

**Note:** Old `showToast` API still works for backward compatibility.

## Support

For questions or issues with error handling:
1. Check this guide first
2. Look at LoginPage.tsx for example implementation
3. Review /api/client.ts for retry logic
4. Check console for retry attempt logs

## Related Files

- `/frontend/src/api/client.ts` - API client with retry logic
- `/frontend/src/utils/toast.ts` - Toast notification utilities
- `/frontend/src/components/ErrorBoundary.tsx` - Error boundary component
- `/frontend/src/store/slices/authSlice.ts` - Auth error handling
- `/frontend/src/pages/LoginPage.tsx` - Example implementation
