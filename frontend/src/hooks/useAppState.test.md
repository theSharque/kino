# State Persistence Test Plan

## Test Scenario: Project and Frame State Persistence

### Steps to Test:

1. **Open Application**
   - Navigate to http://localhost:5173
   - Check browser console for: `📱 App state restored from localStorage:` (should be empty initially)

2. **Create or Open Project**
   - Create a new project or open existing one
   - Check console for: `💾 App state saved to localStorage:` with project ID

3. **Navigate Between Frames**
   - Use arrow keys or click on timeline frames
   - Check console for: `💾 App state saved to localStorage:` with updated frame index

4. **Refresh Browser**
   - Press F5 or Ctrl+R
   - Check console for: `🔄 Restoring project from saved state:` with project ID
   - Verify project is automatically loaded
   - Verify frame index is restored

5. **Close and Reopen Browser**
   - Close browser tab/window completely
   - Reopen browser and navigate to http://localhost:5173
   - Check console for restoration messages
   - Verify state is fully restored

### Expected Behavior:

- **Project Selection**: Automatically restored on app load
- **Frame Index**: Restored to last selected frame
- **Console Logs**: Clear logging of save/restore operations
- **Error Handling**: Graceful fallback if saved project no longer exists

### Test Data Structure:

```json
{
  "currentProjectId": 1,
  "currentFrameIndex": 5,
  "lastUpdated": 1703123456789
}
```

### Browser Storage:

- **Key**: `kino_app_state`
- **Location**: `localStorage`
- **Persistence**: Survives browser restarts
- **Scope**: Per-domain (localhost:5173)

## Success Criteria:

✅ Project automatically loads on app start
✅ Frame index restored correctly
✅ State persists across browser sessions
✅ Error handling works for invalid project IDs
✅ Console logging provides clear feedback
