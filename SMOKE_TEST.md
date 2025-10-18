# Smoke Tests for Kino Application

This document describes automated smoke tests to verify the core functionality of the Kino application.

## ⚠️ Important: Sequential Execution Required

**These smoke tests MUST be executed in strict sequential order.** Each test builds upon the previous one, and skipping or reordering tests will cause failures. Do not run tests in parallel or out of sequence.

## Test Environment Setup

- Backend: Python aiohttp server
- Frontend: React + Vite development server
- Browser: Any modern browser
- Test image size: 512x512 pixels
- Test steps: 5-20 steps (as specified per test)

## Prerequisites

Before running smoke tests, ensure you have:

### Required Software
- **Python 3.12+** (for backend)
- **Node.js LTS** (for frontend, managed via nvm)
- **nvm** (Node Version Manager)
- **Git**

### Backend Setup
```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend

# Activate Node.js LTS
nvm use --lts

# Install dependencies
npm install
```

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

> **Note**: Tests are interdependent and must be run in order:
> - Pre-Test Setup: Clean environment
> - Test 1: Starts servers (required for all subsequent tests)
> - Test 2: Creates project (required for Tests 3-6)
> - Tests 3-4: Generate frames (required for Tests 5-6)
> - Tests 5-6: Test deletion functionality
> - Post-Test Cleanup: Stop servers and clean logs

### Test 1: Application Startup
**Objective**: Verify application starts correctly without errors

**Prerequisites**:
- Python 3.12+ installed
- Node.js LTS installed via nvm
- Backend virtual environment created and dependencies installed
- Frontend dependencies installed

**Steps**:
1. **Start Backend Server**:
   ```bash
   cd backend
   source venv/bin/activate  # Activate virtual environment
   python main.py > server.log 2>&1 &
   ```
   Backend will start on `http://localhost:8000`

2. **Start Frontend Server**:
   ```bash
   cd frontend
   nvm use --lts  # Activate Node.js LTS (REQUIRED!)
   npm run dev > frontend.log 2>&1 &
   ```
   Frontend will start on `http://localhost:5173`

   **Alternative (if nvm is not available)**:
   ```bash
   cd frontend
   ./node_modules/.bin/vite > frontend.log 2>&1 &
   ```
   Note: This requires Node.js to be installed system-wide

3. **Wait for servers to start** (5-10 seconds)

4. **Check Backend Logs**:
   ```bash
   tail -20 backend/server.log
   ```
   Look for: "Server started", "Database initialized", "Generator service initialized"

5. **Check Frontend Logs**:
   ```bash
   tail -20 frontend/frontend.log
   ```
   Look for: "Local: http://localhost:5173/", "ready in Xms"

6. **Open Browser** and navigate to `http://localhost:5173`

7. **Check WebSocket Connection** in browser console:
   - Open Developer Tools (F12)
   - Check Console tab for WebSocket connection messages
   - Look for: "WebSocket connected" or similar messages

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
5. Set fps to 24
6. Click "Create Project"

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
5. Check filesystem for remaining files:
   ```bash
   ls -la backend/data/frames/ | grep frame_
   ```
6. Check database for remaining records:
   ```bash
   cd backend && source venv/bin/activate && python -c "
   import sqlite3
   conn = sqlite3.connect('data/kino.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM frames')
   print(f'Remaining frames: {cursor.fetchone()[0]}')
   conn.close()
   "
   ```

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
6. Check filesystem for remaining files:
   ```bash
   ls -la backend/data/frames/ | grep frame_
   ```
7. Check database for remaining records:
   ```bash
   cd backend && source venv/bin/activate && python -c "
   import sqlite3
   conn = sqlite3.connect('data/kino.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM projects')
   print(f'Remaining projects: {cursor.fetchone()[0]}')
   cursor.execute('SELECT COUNT(*) FROM frames')
   print(f'Remaining frames: {cursor.fetchone()[0]}')
   conn.close()
   "
   ```

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
Monitor `backend/server.log` for these log patterns:
- `[INFO] Server started on http://0.0.0.0:8000`
- `[INFO] WebSocket connection established`
- `[INFO] Starting frame generation for project {project_id}`
- `[INFO] Generated variant {variant_id} for frame {frame_id}`
- `[INFO] Frame generation completed successfully`

### Frontend Log Monitoring
Monitor `frontend/frontend.log` for these log patterns:
- `[INFO] WebSocket connected`
- `[INFO] Frame updated: {frame_id}`
- `[INFO] Preview image updated`
- `[INFO] Generation completed`

### File System Verification
Check these directories:
- `backend/data/frames/` - Should contain generated images and JSON parameter files
- Database: `backend/data/kino.db` - Should contain project and frame records

### Error Indicators
Watch for these error patterns:
- `[ERROR]` messages in logs
- WebSocket connection failures
- HTTP 500 errors
- File system permission errors
- Database constraint violations

## Post-Test Cleanup

### Stop All Servers and Clean Logs
**Objective**: Clean up test environment and remove old logs

**Steps**:
1. **Stop Backend Server**:
   ```bash
   pkill -f "python.*main.py"
   ```

2. **Stop Frontend Server**:
   ```bash
   pkill -f "vite\|npm.*dev"
   ```

3. **Wait for processes to terminate** (2-3 seconds)

4. **Verify servers are stopped**:
   ```bash
   netstat -tulpn | grep :8000  # Should be empty
   netstat -tulpn | grep :5173  # Should be empty
   ```

5. **Clean up log files**:
   ```bash
   rm -f backend/server.log
   rm -f frontend/frontend.log
   ```

6. **Verify log files are removed**:
   ```bash
   ls -la backend/server.log 2>/dev/null || echo "Backend log cleaned"
   ls -la frontend/frontend.log 2>/dev/null || echo "Frontend log cleaned"
   ```

**Expected Results**:
- ✅ No backend processes running on port 8000
- ✅ No frontend processes running on port 5173
- ✅ Backend log file removed
- ✅ Frontend log file removed
- ✅ Clean environment ready for next test run

---

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
1. **Check backend logs** for detailed error messages:
   ```bash
   tail -50 backend/server.log
   ```
2. **Check frontend logs** for JavaScript errors:
   ```bash
   tail -50 frontend/frontend.log
   ```
3. **Monitor logs in real-time** during tests:
   ```bash
   tail -f backend/server.log  # Backend logs
   tail -f frontend/frontend.log  # Frontend logs
   ```
4. **Verify file system permissions**
5. **Verify database integrity**
6. **Check WebSocket connection status**
7. **Verify all required dependencies are installed**

### Common Issues

**Frontend won't start**:
- Ensure Node.js LTS is installed via nvm: `nvm use --lts`
- If nvm is not available, install Node.js system-wide
- Check if dependencies are installed: `npm install`

**Backend won't start**:
- Ensure Python 3.12+ is installed
- Check if virtual environment is activated: `source venv/bin/activate`
- Verify dependencies are installed: `pip install -r requirements.txt`

**Port conflicts**:
- Check if ports 8000 or 5173 are already in use
- Stop conflicting services or change ports in configuration
