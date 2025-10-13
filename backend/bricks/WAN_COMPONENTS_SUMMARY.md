# Wan Bricks Components Summary

## Краткая справка по компонентам

### Созданные компоненты (wan_bricks.py)

| # | Компонент | Вход | Выход | Назначение |
|---|-----------|------|-------|------------|
| 1 | **load_clip_vision** | `clip_name: str` | `clip_vision` | Загрузка CLIP Vision модели для кодирования изображений |
| 2 | **clip_vision_encode** | `clip_vision`, `image`, `crop='center'` | `clip_vision_output` | Кодирование изображения в CLIP Vision эмбеддинги |
| 3 | **load_vae** | `vae_name: str` | `vae` | Загрузка VAE для кодирования/декодирования изображений |
| 4 | **load_clip** | `clip_name: str`, `clip_type='wan'`, `device='default'` | `clip` | Загрузка CLIP text encoder (поддерживает GGUF) |
| 5 | **wan_image_to_video** | `positive`, `negative`, `vae`, `width=832`, `height=480`, `length=81`, `batch_size=1`, `clip_vision_output=None`, `start_image=None` | `(positive, negative, latent)` | Подготовка conditioning и latent для генерации видео |

---

## Входные и выходные параметры

### 1. Load CLIP Vision
```python
load_clip_vision(clip_name: str) → clip_vision
```
**Вход:**
- `clip_name` - имя файла модели из `models/clip_vision/`

**Выход:**
- `clip_vision` - объект CLIP Vision модели

**Пример:**
```python
clip_vision = load_clip_vision("clip_vision_g.safetensors")
```

---

### 2. CLIP Vision Encode
```python
clip_vision_encode(clip_vision, image, crop='center') → clip_vision_output
```
**Вход:**
- `clip_vision` - модель из `load_clip_vision()`
- `image` - изображение `torch.Tensor [B, H, W, C]`
- `crop` - метод кропа: `'center'` или `'none'`

**Выход:**
- `clip_vision_output` - эмбеддинг типа CLIP_VISION_OUTPUT

**Пример:**
```python
output = clip_vision_encode(clip_vision, image, crop="center")
```

---

### 3. Load VAE
```python
load_vae(vae_name: str) → vae
```
**Вход:**
- `vae_name` - имя файла VAE из `models/vae/` или специальное имя
  - Файлы: `*.safetensors`, `*.pt`
  - Специальные: `"pixel_space"`, `"taesd"`, `"taesdxl"`, `"taesd3"`, `"taef1"`

**Выход:**
- `vae` - объект VAE модели

**Пример:**
```python
vae = load_vae("wan_2.1_vae.safetensors")
```

---

### 4. Load CLIP (Text Encoder)
```python
load_clip(clip_name: str, clip_type: str = 'wan', device: str = 'default') → clip
```
**Вход:**
- `clip_name` - имя файла CLIP из `models/text_encoders/`
- `clip_type` - тип модели (по умолчанию `'wan'`):
  - `"wan"` - для Wan моделей
  - `"sd3"`, `"flux"`, `"stable_diffusion"` и др.
- `device` - устройство: `"default"` или `"cpu"`

**Выход:**
- `clip` - объект CLIP text encoder

**Пример:**
```python
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")
# или квантизованная GGUF версия:
clip = load_clip("umt5_xxl_q8_0.gguf", clip_type="wan")
```

---

### 5. Wan Image to Video
```python
wan_image_to_video(
    positive, negative, vae,
    width=832, height=480, length=81, batch_size=1,
    clip_vision_output=None, start_image=None
) → (positive, negative, latent)
```
**Вход:**
- `positive` - positive conditioning из CLIP
- `negative` - negative conditioning из CLIP
- `vae` - VAE модель
- `width` - ширина видео (по умолчанию 832)
- `height` - высота видео (по умолчанию 480)
- `length` - длина в кадрах (по умолчанию 81, должно быть `length % 4 == 1`)
- `batch_size` - размер батча (по умолчанию 1)
- `clip_vision_output` - опционально, CLIP Vision эмбеддинг референсного изображения
- `start_image` - опционально, стартовый кадр `torch.Tensor [1, H, W, 3]`

**Выход:**
- `positive` - модифицированный positive conditioning
- `negative` - модифицированный negative conditioning
- `latent` - словарь с ключом `"samples"` (пустой latent тензор)

**Пример:**
```python
positive, negative, latent = wan_image_to_video(
    positive=pos_cond,
    negative=neg_cond,
    vae=vae,
    width=832,
    height=480,
    length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)
```

---

## Полный пример использования

```python
from bricks.wan_bricks import (
    load_clip, load_clip_vision, clip_vision_encode,
    load_vae, wan_image_to_video
)
from bricks.comfy_bricks import clip_encode

# 1. Загрузка моделей
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")
clip_vision = load_clip_vision("clip_vision_g.safetensors")
vae = load_vae("wan_2.1_vae.safetensors")

# 2. Кодирование текста
positive = clip_encode(clip, "a beautiful cat walking in garden")
negative = clip_encode(clip, "blurry, low quality")

# 3. Кодирование референсного изображения (опционально)
clip_vision_output = clip_vision_encode(
    clip_vision, reference_image, crop="center"
)

# 4. Подготовка видео генерации
positive, negative, latent = wan_image_to_video(
    positive=positive,
    negative=negative,
    vae=vae,
    width=832,
    height=480,
    length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)

# 5. Использование с сэмплером (из comfy_bricks)
# from bricks.comfy_bricks import common_ksampler
# samples, seed = common_ksampler(
#     model=wan_model,  # Wan diffusion модель
#     latent=latent,
#     positive=positive,
#     negative=negative,
#     steps=20,
#     cfg=7.0
# )

# 6. Декодирование видео
# from bricks.comfy_bricks import vae_decode
# video_frames = vae_decode(vae, samples)
```

---

## Структура Latent для Wan

Wan использует специальную структуру latent:
- **Каналы**: 16 (вместо 4 для SD)
- **Временное измерение**: `((length - 1) // 4) + 1`
- **Пространственные размеры**: `height // 8` × `width // 8`
- **Форма тензора**: `[batch, 16, temporal, height//8, width//8]`

### Ограничения по длине видео

Длина видео должна удовлетворять: `length % 4 == 1`

Допустимые значения:
- 17 кадров (4 секунды @ 4fps)
- 33 кадра (8 секунд @ 4fps)
- 49 кадров (12 секунд @ 4fps)
- 81 кадр (20 секунд @ 4fps)
- и т.д.

Это связано с коэффициентом временного сжатия 4 в VAE.

---

## Необходимые модели

Для генерации видео Wan нужны:

1. **CLIP Text Encoder**: `umt5_xxl` для Wan моделей
   - Расположение: `models/text_encoders/`
   - Поддерживает GGUF квантизацию

2. **CLIP Vision** (опционально): для conditioning по изображению
   - Расположение: `models/clip_vision/`
   - Пример: `clip_vision_g.safetensors`

3. **VAE**: специфичный для Wan
   - Расположение: `models/vae/`
   - Пример: `wan_2.1_vae.safetensors`

4. **Diffusion Model**: Wan checkpoint
   - Расположение: `models/checkpoints/` или `models/diffusion_models/`
   - Примеры: Wan 2.1, Wan 2.2

---

## Файлы

- **`wan_bricks.py`** - основной модуль с функциями
- **`README_WAN.md`** - подробная документация
- **`test_wan_bricks.py`** - тестовый скрипт для проверки
- **`WAN_COMPONENTS_SUMMARY.md`** - этот файл (краткая справка)

---

## Источники

Код основан на:
- `nodes.py` из ComfyUI (CLIPVisionLoader, CLIPVisionEncode, VAELoader, CLIPLoader)
- `comfy_extras/nodes_wan.py` из ComfyUI (WanImageToVideo)

Полная реализация: https://github.com/comfyanonymous/ComfyUI

