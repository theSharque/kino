# Smoke Tests for Kino Application

This document describes automated smoke tests to verify the core functionality of the Kino application.

## Test Environment Setup

- Backend: Python aiohttp server
- Frontend: React + Vite development server
- Browser: Any modern browser
- Test image size: 512x512 pixels
- Test steps: 5-20 steps (as specified per test)

## Pre-Test Setup

### Check and Stop Running Servers
**Objective**: Ensure clean test environment by stopping any running servers

**Steps**:
1. Check for running backend processes:
   ```bash
   ps aux | grep "python.*main.py" | grep -v grep
   ```
2. Check for running frontend processes:
   ```bash
   ps aux | grep "vite\|npm.*dev" | grep -v grep
   ```
3. If backend is running, stop it:
   ```bash
   pkill -f "python.*main.py"
   ```
4. If frontend is running, stop it:
   ```bash
   pkill -f "vite\|npm.*dev"
   ```
5. Wait 2-3 seconds for processes to fully terminate
6. Verify no servers are running:
   ```bash
   netstat -tulpn | grep :8000  # Backend port
   netstat -tulpn | grep :5173  # Frontend port
   ```

**Expected Results**:
- ✅ No backend processes running on port 8000
- ✅ No frontend processes running on port 5173
- ✅ Clean environment ready for testing

---

## Test Cases

### Test 1: Application Startup
**Objective**: Verify application starts correctly without errors

**Steps**:
1. Start backend server (`cd backend && python main.py`)
2. Start frontend server (`cd frontend && npm run dev`)
3. Check backend logs for any startup errors
4. Check frontend logs for any startup errors
5. Open browser and navigate to frontend URL (typically `http://localhost:5173`)

**Expected Results**:
- ✅ Backend server starts without errors
- ✅ Frontend server starts without errors
- ✅ Application is visible in browser
- ✅ No error messages in console logs
- ✅ WebSocket connection established

---

### Test 2: Project Creation
**Objective**: Verify project creation functionality

**Steps**:
1. Click on "Projects" menu button
2. Click "New Project" button
3. Enter project name (e.g., "Smoke Test Project")
4. Set project dimensions to 512x512
5. Click "Create Project"

**Expected Results**:
- ✅ New project appears in projects list
- ✅ Project is automatically selected
- ✅ Project data is saved to database
- ✅ No error messages in logs

---

### Test 3: Single Frame Generation
**Objective**: Verify basic frame generation with preview updates

**Steps**:
1. Ensure a project is selected
2. Click "Generate Frame" button
3. Select SDXL generator
4. Set parameters:
   - Width: 512
   - Height: 512
   - Steps: 20
   - Prompt: "A beautiful landscape"
   - Seed: (auto-generated)
5. Click "Generate"
6. Monitor backend logs during generation
7. Monitor frontend for preview updates

**Expected Results**:
- ✅ Generation starts successfully
- ✅ Backend logs show generation progress
- ✅ Frontend shows preview images updating during generation
- ✅ Final frame appears in timeline
- ✅ Frame image is saved to filesystem
- ✅ Frame parameters are saved to JSON file
- ✅ Database record is created

---

### Test 4: Multiple Variants Generation
**Objective**: Verify frame variants functionality

**Steps**:
1. Ensure a project is selected
2. Click "Generate Frame" button
3. Select SDXL generator
4. Set parameters:
   - Width: 512
   - Height: 512
   - Steps: 5
   - Prompt: "A beautiful landscape"
   - Seed: (auto-generated)
   - Variants: 5
5. Click "Generate"
6. Monitor backend logs during generation
7. Monitor frontend for preview updates

**Expected Results**:
- ✅ Generation starts successfully
- ✅ Backend logs show creation of 5 variants
- ✅ Frontend shows preview images updating
- ✅ 5 variant files are created (e.g., `frame_1_v0.png`, `frame_1_v1.png`, etc.)
- ✅ 5 JSON parameter files are created
- ✅ 5 database records are created with variant_id 0-4
- ✅ Frame viewer shows variant navigation controls
- ✅ User can navigate between variants using prev/next buttons

---

### Test 5: Frame Deletion
**Objective**: Verify frame deletion removes all associated files

**Steps**:
1. Ensure a frame exists (from previous tests)
2. Right-click on the frame in timeline
3. Select "Delete Frame" from context menu
4. Confirm deletion
5. Check filesystem for remaining files
6. Check database for remaining records

**Expected Results**:
- ✅ Frame is removed from timeline
- ✅ All variant image files are deleted from filesystem
- ✅ All variant JSON parameter files are deleted
- ✅ All database records for the frame variants are deleted
- ✅ No orphaned files remain

---

### Test 6: Project Deletion
**Objective**: Verify project deletion removes all associated data

**Steps**:
1. Ensure a project with frames exists (from previous tests)
2. Click on "Projects" menu button
3. Find the test project
4. Click delete button for the project
5. Confirm deletion
6. Check filesystem for remaining files
7. Check database for remaining records

**Expected Results**:
- ✅ Project is removed from projects list
- ✅ All frames associated with the project are deleted
- ✅ All frame image files are deleted from filesystem
- ✅ All frame JSON parameter files are deleted
- ✅ All database records for the project and its frames are deleted
- ✅ No orphaned files or database records remain

---

## Test Execution Notes

### Backend Log Monitoring
Look for these log patterns:
- `[INFO] Server started on http://0.0.0.0:8000`
- `[INFO] WebSocket connection established`
- `[INFO] Starting frame generation for project {project_id}`
- `[INFO] Generated variant {variant_id} for frame {frame_id}`
- `[INFO] Frame generation completed successfully`

### Frontend Log Monitoring
Look for these log patterns:
- `[INFO] WebSocket connected`
- `[INFO] Frame updated: {frame_id}`
- `[INFO] Preview image updated`
- `[INFO] Generation completed`

### File System Verification
Check these directories:
- `backend/data/frames/` - Should contain generated images
- `backend/data/frames/` - Should contain JSON parameter files
- Database: `backend/data/kino.db` - Should contain project and frame records

### Error Indicators
Watch for these error patterns:
- `[ERROR]` messages in logs
- WebSocket connection failures
- HTTP 500 errors
- File system permission errors
- Database constraint violations

## Test Data Cleanup

After running smoke tests, clean up test data:
1. Delete any test projects created
2. Verify no test files remain in `backend/data/frames/`
3. Check database for any orphaned records

## Success Criteria

All tests must pass for the application to be considered stable:
- ✅ Application starts without errors
- ✅ Core CRUD operations work (Create, Read, Update, Delete)
- ✅ File system operations work correctly
- ✅ Database operations work correctly
- ✅ WebSocket communication works
- ✅ Preview generation works
- ✅ Frame variants work
- ✅ Cleanup operations work

## Troubleshooting

If tests fail:
1. Check backend logs for detailed error messages
2. Check frontend console for JavaScript errors
3. Verify file system permissions
4. Verify database integrity
5. Check WebSocket connection status
6. Verify all required dependencies are installed
