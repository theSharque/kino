# ComfyUI Installation Required

This directory should contain a full ComfyUI installation.

## Installation

Clone the official ComfyUI repository into this directory:

```bash
cd /qs/kino/backend
git clone https://github.com/comfyanonymous/ComfyUI.git ComfyUI
```

## Verification

After cloning, verify the installation:

```bash
cd /qs/kino/backend
ls -la ComfyUI/comfy/  # Should show ComfyUI core files
```

You should see files like:
- `sample.py`
- `samplers.py`
- `sd.py`
- `model_management.py`
- etc.

## Test Integration

Test that Kino can use ComfyUI:

```bash
cd /qs/kino/backend/bricks
source ../venv/bin/activate
python test_comfy_integration.py
```

Expected output:
```
✅ All tests passed!
🎉 Ready to use full ComfyUI!
```

## Version Compatibility

- **Tested with:** ComfyUI main branch (as of October 2025)
- **Minimum required:** ComfyUI with `comfy/samplers.py` containing KSAMPLER_NAMES

## Why Not Included in Git?

ComfyUI is a large repository (~500MB+) with frequent updates. Instead of including it:

1. **Smaller repo size** - Kino repo stays lightweight
2. **Easy updates** - Just `git pull` in ComfyUI directory
3. **Clean separation** - ComfyUI is external dependency
4. **No duplication** - Use official ComfyUI repository

## Integration Details

Kino integrates ComfyUI via the `bricks/` layer:

- **Bricks automatically adds ComfyUI to sys.path**
- Plugins use bricks, not ComfyUI directly
- See `/backend/COMFYUI_INTEGRATION.md` for details

## Troubleshooting

### "No module named 'comfy'" Error

**Cause:** ComfyUI not installed in this directory

**Solution:**
```bash
cd /qs/kino/backend
git clone https://github.com/comfyanonymous/ComfyUI.git ComfyUI
```

### "No module named 'torchsde'" Error

**Cause:** ComfyUI dependencies not installed

**Solution:**
```bash
cd /qs/kino/backend
source venv/bin/activate
pip install -r requirements.txt
```

All ComfyUI dependencies are included in Kino's requirements.txt.

## Directory Structure After Installation

```
backend/
├── ComfyUI/                    # ← Git clone here
│   ├── comfy/                 # Core library
│   ├── comfy_api/             # API modules
│   ├── comfy_extras/          # Extra nodes
│   ├── custom_nodes/          # Custom nodes
│   ├── models/                # Model storage
│   ├── main.py                # ComfyUI server
│   └── README.md (this file)
│
├── bricks/                     # Kino's ComfyUI wrapper
│   └── comfy_bricks.py        # Uses ComfyUI via sys.path
│
└── COMFYUI_INTEGRATION.md     # Integration guide
```

## Notes

- ComfyUI's own server (`main.py`) is **not used** by Kino
- Kino uses only ComfyUI's library functions via bricks
- Models are stored in `/backend/models_storage/`, not ComfyUI's models/
- This approach keeps Kino independent while leveraging ComfyUI's power

---

**For detailed integration information, see:** `/backend/COMFYUI_INTEGRATION.md`
