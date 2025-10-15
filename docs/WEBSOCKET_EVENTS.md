# WebSocket Events Documentation

## Overview

The Kino application uses WebSocket for real-time communication between backend and frontend. This allows for automatic updates without manual page refreshes.

## Connection

- **Endpoint**: `ws://localhost:8000/ws`
- **Reconnection**: Automatic reconnection with 3-second delay on disconnect
- **Heartbeat**: 10-second heartbeat to keep connection alive

## Event Types

### 1. Metrics Update (`metrics`)

Sent every 2 seconds with system metrics and task queue status.

**Direction**: Backend → Frontend

**Payload**:
```json
{
  "type": "metrics",
  "data": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "gpu_percent": 80.5,
    "gpu_memory_percent": 75.3,
    "gpu_available": true,
    "gpu_type": "cuda",
    "pending_count": 5,
    "running_count": 1,
    "current_task": {
      "id": 42,
      "name": "Generate frame",
      "progress": 65.0
    }
  }
}
```

**Frontend Usage**:
- Displayed in MenuBar (system metrics)
- Shows current task progress
- Updates queue status (pending+running)

---

### 2. Frame Update (`frame_updated`)

Sent when a frame is created or updated (e.g., after generation completes).

**Direction**: Backend → Frontend

**Payload**:
```json
{
  "type": "frame_updated",
  "data": {
    "frame_id": 42,
    "project_id": 8,
    "path": "/qs/kino/backend/data/frames/task_42_20251015_123456.png",
    "generator": "sdxl",
    "created_at": "2025-10-15T12:34:56.789012",
    "updated_at": "2025-10-15T12:34:56.789012"
  }
}
```

**Frontend Behavior**:
1. Check if frame belongs to currently open project
2. Fetch full frame data via `/api/v1/frames/{frame_id}`
3. Update or add frame to the timeline
4. If frame is currently selected, update the main viewer

**Use Cases**:
- Automatic frame refresh after generation
- Real-time preview updates
- Multi-user collaboration (future)

---

## Client Messages

### Ping (`ping`)

Client can send ping to check connection.

**Direction**: Frontend → Backend

**Request**:
```json
{
  "type": "ping"
}
```

**Response**:
```json
{
  "type": "pong"
}
```

---

### Close (`close`)

Client can gracefully close connection.

**Direction**: Frontend → Backend

**Payload**:
```json
{
  "type": "close"
}
```

---

## Implementation

### Backend

**Broadcasting Events**:
```python
from handlers.websocket import broadcast_message

# Send frame update event
await broadcast_message({
    'type': 'frame_updated',
    'data': {
        'frame_id': frame.id,
        'project_id': frame.project_id,
        'path': frame.path,
        'generator': frame.generator,
        'created_at': frame.created_at,
        'updated_at': frame.updated_at
    }
})
```

**Location**: `backend/handlers/websocket.py`

---

### Frontend

**Handling Events**:
```typescript
import { useWebSocket, FrameUpdateEvent } from './hooks/useWebSocket';

const handleFrameUpdate = useCallback(
  async (event: FrameUpdateEvent) => {
    if (currentProject && event.project_id === currentProject.id) {
      const updatedFrame = await framesAPI.getFrame(event.frame_id);
      // Update state...
    }
  },
  [currentProject]
);

const { metrics, isConnected } = useWebSocket(handleFrameUpdate);
```

**Location**: `frontend/src/hooks/useWebSocket.ts`

---

## Future Events

Potential events to implement:

- `task_started` - Task generation started
- `task_progress` - Task progress update (more granular than metrics)
- `task_completed` - Task completed (success or failure)
- `project_updated` - Project settings changed
- `frame_deleted` - Frame deleted
- `preview_updated` - Preview image updated during generation
- `user_action` - Another user performed an action (for collaboration)

---

## Error Handling

- **Connection Lost**: Frontend automatically reconnects
- **Invalid JSON**: Logged to console, ignored
- **Unknown Event Type**: Logged to console, ignored
- **Broadcast Failure**: Backend logs error, removes disconnected clients

---

## Performance Considerations

- Metrics sent every 2 seconds (configurable)
- Frame updates sent only when necessary
- Broadcast uses `WeakSet` for automatic cleanup
- No message queue - events are fire-and-forget

---

## Testing

1. Open browser console
2. Connect to the app
3. Trigger events (e.g., generate frame)
4. Observe console logs:
   - `📡 WebSocket connected`
   - `📸 Frame updated: {...}`
   - `Handling frame update: {...}`

---

## Troubleshooting

**Issue**: WebSocket disconnects frequently
- **Solution**: Check network stability, firewall rules

**Issue**: Events not received
- **Solution**: Check browser console for connection status, verify backend is sending events

**Issue**: Frontend doesn't update
- **Solution**: Verify callback is properly registered in `useWebSocket`

**Issue**: Old frames don't update
- **Solution**: Frame updates only apply to currently open project

