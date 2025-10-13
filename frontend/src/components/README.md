# Kino Frontend Components

React components for the Kino video editor interface.

**Last Updated:** 2025-10-13 - Added project dimensions auto-fill in GenerateFrameModal

## Main Components

### FrameViewer

Upper section component (70% of screen) that displays the current frame and playback controls.

**Location:** `src/components/FrameViewer.tsx`

**Props:**
```typescript
interface FrameViewerProps {
  currentFrameIndex: number;    // Current frame index (0-based)
  totalFrames: number;          // Total number of frames
  fps: number;                  // Frames per second
  isPlaying: boolean;           // Playback state
  onFrameChange: (index: number) => void;  // Frame navigation callback
  onPlayPause: () => void;      // Play/Pause toggle callback
  frameImageUrl?: string;       // URL of current frame image
}
```

**Features:**
- ⏮ Go to first frame
- ⏪ Previous frame
- ▶/⏸ Play/Pause toggle
- ⏩ Next frame
- ⏭ Go to last frame
- Frame counter display (current/total)
- FPS indicator
- Responsive image display (fit to container)

**Styling:** Dark theme with hover effects and disabled states

---

### Timeline

Lower section component (30% of screen) that displays frames as a filmstrip with horizontal scrolling.

**Location:** `src/components/Timeline.tsx`

**Props:**
```typescript
interface Frame {
  id: number;              // Unique frame ID
  index: number;           // Frame index in sequence
  thumbnailUrl?: string;   // Thumbnail image URL
  path?: string;           // Full image path
}

interface TimelineProps {
  frames: Frame[];                      // Array of frames to display
  currentFrameIndex: number;            // Currently selected frame
  onFrameSelect: (index: number) => void;  // Frame selection callback
}
```

**Features:**
- Horizontal scrollable filmstrip view
- Click to select frame
- Auto-scroll to selected frame (smooth scrolling)
- Lazy loading images (`loading="lazy"`)
- Visual indication of selected frame (highlight + scale)
- Frame number overlay
- Empty state placeholder

**Optimization:**
- Images loaded only when needed (native lazy loading)
- Smooth scroll behavior
- Will use `react-window` for true virtual scrolling when implemented

**Styling:** Dark filmstrip theme with custom scrollbar

---

## Layout Structure

```
┌─────────────────────────────────────┐
│                                     │
│        FrameViewer (70%)            │
│    ┌─────────────────────┐          │
│    │   Current Frame     │          │
│    │     Display         │          │
│    └─────────────────────┘          │
│    [⏮] [⏪] [▶] [⏩] [⏭] 1/100      │
│                                     │
├─────────────────────────────────────┤
│                                     │
│       Timeline (30%)                │
│  [F1][F2][F3][F4][F5] → scroll →   │
│                                     │
└─────────────────────────────────────┘
```

## State Management

Currently managed in `App.tsx`:

```typescript
const [frames, setFrames] = useState<Frame[]>([]);
const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
const [isPlaying, setIsPlaying] = useState(false);
const [fps, setFps] = useState(24);
```

**Future:** Consider Context API or state management library for complex state.

## Keyboard Shortcuts

Implemented in `App.tsx`:

- `←` Left Arrow - Previous frame
- `→` Right Arrow - Next frame
- `Space` or `K` - Play/Pause
- `Home` - Go to first frame
- `End` - Go to last frame

## Playback Implementation

Playback uses `setInterval` with frame rate calculated from FPS:

```typescript
const interval = 1000 / fps; // milliseconds per frame

setInterval(() => {
  setCurrentFrameIndex(prev => prev + 1);
}, interval);
```

- Automatically stops at the end
- Cleans up interval on pause/unmount
- Pauses when manually selecting a frame

## Next Steps

### Integration with Backend

1. **Load frames from API:**
```typescript
const fetchFrames = async (projectId: number) => {
  const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/frames`);
  const data = await response.json();
  return data.frames;
};
```

2. **Load frame images:**
```typescript
const frameUrl = `http://localhost:8000/data/frames/${frame.path}`;
```

### Virtual Scrolling with react-window

Replace current Timeline with `FixedSizeList`:

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={150}
  itemCount={frames.length}
  itemSize={130}
  width="100%"
  layout="horizontal"
>
  {({ index, style }) => (
    <div style={style}>
      <FrameThumbnail frame={frames[index]} />
    </div>
  )}
</FixedSizeList>
```

### Additional Features

- [ ] Zoom controls for frame viewer
- [ ] Loop playback option
- [ ] Variable playback speed
- [ ] Frame range selection
- [ ] Drag-and-drop frame reordering
- [ ] Thumbnail generation from frames
- [ ] Cache management for loaded images

## File Structure

```
src/components/
├── README.md              # This file
├── FrameViewer.tsx        # Upper section component
├── FrameViewer.css        # FrameViewer styles
├── Timeline.tsx           # Lower section component
└── Timeline.css           # Timeline styles
```

## Development

### Run dev server:
```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:5173

### Build for production:
```bash
npm run build
```

## Modal Components

### GenerateFrameModal

Dynamic form generator for creating frames using selected plugin.

**Location:** `src/components/modals/GenerateFrameModal.tsx`

**Props:**
```typescript
interface GenerateFrameModalProps {
  isOpen: boolean;
  onClose: () => void;
  plugin: PluginInfo | null;
  projectId: number | null;
  projectWidth?: number;   // 🆕 Auto-fills width field
  projectHeight?: number;  // 🆕 Auto-fills height field
  onGenerate: (pluginName: string, parameters: Record<string, any>) => void;
}
```

**Features:**
- **Dynamic form generation** from plugin parameter definitions
- **Smart defaults** - Project dimensions override plugin defaults
  - Width: Uses `projectWidth` if provided, otherwise plugin default
  - Height: Uses `projectHeight` if provided, otherwise plugin default
  - Visual indicator: "(from project)" label when using project dimensions
- **Parameter types supported:**
  - `string` - Text input or textarea
  - `integer` - Number input (step=1)
  - `float` - Decimal input (step=0.01)
  - `selection` - Dropdown with predefined options
  - `model_selection` - Auto-populated from backend models
  - `lora_list` - Dynamic LoRA list component
- **Field validation** - Required fields, min/max ranges
- **Model auto-loading** - Fetches available models from backend
- **Null-safe defaults** - Handles null default values correctly

**Example Usage:**
```typescript
<GenerateFrameModal
  isOpen={isOpen}
  onClose={handleClose}
  plugin={selectedPlugin}
  projectId={currentProject?.id || null}
  projectWidth={currentProject?.width}    // 🆕 Auto-fills width
  projectHeight={currentProject?.height}  // 🆕 Auto-fills height
  onGenerate={handleGenerate}
/>
```

**Benefits:**
- Generates frames that match project dimensions by default
- No need to manually adjust width/height for each generation
- Clear visual feedback when using project dimensions
- Can still override if needed

---

## Dependencies

- **react**: ^19.1.1 - React framework
- **react-dom**: ^19.1.1 - React DOM renderer
- **react-window**: ^1.8.10 - Virtual scrolling (to be used)
- **typescript**: ~5.9.3 - TypeScript compiler
- **vite**: ^7.1.7 - Build tool

