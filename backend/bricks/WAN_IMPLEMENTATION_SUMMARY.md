# Wan Bricks Implementation Summary

## Что было сделано

Создан модуль `wan_bricks` для генерации видео с использованием Wan (万物) моделей на основе ComfyUI.

## Созданные файлы

### 1. Основной модуль
- **`wan_bricks.py`** (8.9 KB)
  - 5 основных функций для работы с Wan
  - Все функции с подробными docstrings
  - Импорты из полной установки ComfyUI
  - Типизация и обработка ошибок

### 2. Документация
- **`README_WAN.md`** (7.4 KB)
  - Подробное описание всех функций
  - Примеры использования
  - Требования к моделям
  - Архитектурные детали

- **`WAN_COMPONENTS_SUMMARY.md`** (8.4 KB)
  - Краткая справочная таблица
  - Входы/выходы каждого компонента
  - Полный пример workflow
  - Структура latent тензоров

- **`WAN_WORKFLOW_DIAGRAM.md`** (17.1 KB)
  - ASCII диаграммы потока данных
  - Визуализация шагов генерации
  - Схемы форм тензоров
  - Схема conditioning

### 3. Тестирование
- **`test_wan_bricks.py`** (6.7 KB)
  - Тест импортов
  - Отображение сигнатур функций
  - Таблица входов/выходов
  - Примеры использования

### 4. Обновления
- **`README.md`** (обновлен)
  - Добавлена секция "Wan Video Generation Bricks"
  - Ссылки на новую документацию
  - Быстрый пример использования

## Реализованные компоненты

### 1. Load CLIP Vision
```python
load_clip_vision(clip_name: str) → clip_vision
```
Загрузка CLIP Vision модели для кодирования изображений.

**Источник:** `CLIPVisionLoader` из `nodes.py:985-1000`

---

### 2. CLIP Vision Encode
```python
clip_vision_encode(clip_vision, image, crop='center') → clip_vision_output
```
Кодирование изображения в CLIP Vision эмбеддинги.

**Источник:** `CLIPVisionEncode` из `nodes.py:1002-1019`

---

### 3. Load VAE
```python
load_vae(vae_name: str) → vae
```
Загрузка VAE модели. Поддерживает:
- Стандартные `.safetensors` файлы
- TAESD (Tiny AutoEncoder) модели
- Специальный `"pixel_space"` режим

**Источник:** `VAELoader` из `nodes.py:694-786`

---

### 4. Load CLIP (Text Encoder)
```python
load_clip(clip_name: str, clip_type: str = 'wan', device: str = 'default') → clip
```
Загрузка CLIP text encoder. **Поддерживает GGUF формат!**

**Поддерживаемые типы:**
- `"wan"` - для Wan моделей (по умолчанию)
- `"sd3"`, `"flux"`, `"stable_diffusion"` и др.

**Источник:** `CLIPLoader` из `nodes.py:928-953`

---

### 5. Wan Image to Video
```python
wan_image_to_video(
    positive, negative, vae,
    width=832, height=480, length=81,
    batch_size=1,
    clip_vision_output=None,
    start_image=None
) → (positive, negative, latent)
```
Подготовка conditioning и latent для генерации видео.

**Особенности:**
- Создает пустой latent с формой `[batch, 16, temporal, H/8, W/8]`
- Обрабатывает стартовое изображение (encoding + masking)
- Добавляет CLIP Vision conditioning
- Готовит все необходимое для сэмплинга

**Источник:** `WanImageToVideo` из `comfy_extras/nodes_wan.py:15-60`

## Архитектурные особенности

### Latent Structure
Wan использует уникальную структуру latent:
- **16 каналов** (вместо 4 у SD)
- **Временное сжатие 4x**: `T = ((length-1)//4)+1`
- **Пространственное сжатие 8x**: `H/8 × W/8`

### Ограничения
- Длина видео: `length % 4 == 1` (17, 33, 49, 81, 97, ...)
- Пространственные размеры: кратны 8

### Conditioning
Wan поддерживает несколько типов conditioning:
1. **Text** - CLIP text embeddings
2. **CLIP Vision** - image embeddings
3. **Concat Latent** - encoded start/control images
4. **Concat Mask** - маска областей для denoising

## Типичный Workflow

```python
# 1. Загрузка моделей
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")
clip_vision = load_clip_vision("clip_vision_g.safetensors")
vae = load_vae("wan_2.1_vae.safetensors")

# 2. Кодирование текста
positive = clip_encode(clip, "a cat walking")
negative = clip_encode(clip, "blurry")

# 3. Кодирование изображения (опционально)
clip_vision_output = clip_vision_encode(clip_vision, image)

# 4. Подготовка видео
positive, negative, latent = wan_image_to_video(
    positive, negative, vae,
    width=832, height=480, length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)

# 5. Сэмплинг
samples, seed = common_ksampler(
    model, latent, positive, negative,
    steps=20, cfg=7.0
)

# 6. Декодирование
video = vae_decode(vae, samples)
```

## Интеграция с ComfyUI

### Импорты из ComfyUI
Модуль использует прямые импорты из полной установки ComfyUI:
```python
import comfy.clip_vision
import comfy.model_management
import comfy.sd
import comfy.utils
import folder_paths
import node_helpers
```

### Динамическое добавление в sys.path
```python
comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))
```

### Подавление предупреждений линтера
Импорты помечены `# type: ignore` так как линтер не видит динамически добавленные пути.

## Требования к моделям

### Обязательные
1. **CLIP Text Encoder**: `umt5_xxl` (или GGUF версия)
2. **VAE**: `wan_2.1_vae.safetensors` или `wan_2.2_vae.safetensors`
3. **Diffusion Model**: Wan 2.1 или 2.2 checkpoint

### Опциональные
1. **CLIP Vision**: `clip_vision_g.safetensors` (для image conditioning)

### Расположение
```
models_storage/
├── text_encoders/
│   └── umt5_xxl.safetensors
├── clip_vision/
│   └── clip_vision_g.safetensors
├── vae/
│   └── wan_2.1_vae.safetensors
└── checkpoints/
    └── wan_2.1.safetensors
```

## Тестирование

### Запуск тестов
```bash
cd /qs/kino/backend
python bricks/test_wan_bricks.py
```

### Результат
```
✓ All imports successful!

Function Signatures:
...

Input/Output Summary:
...

Complete Workflow Example:
...
```

## Совместимость

- **Python**: 3.12+
- **PyTorch**: С поддержкой CUDA/XPU
- **ComfyUI**: Полная установка (не stripped версия)
- **OS**: Linux, Windows, macOS

## Ссылки на исходники

### ComfyUI Nodes
1. **CLIPVisionLoader**: `/qs/kino/backend/ComfyUI/nodes.py:985-1000`
2. **CLIPVisionEncode**: `/qs/kino/backend/ComfyUI/nodes.py:1002-1019`
3. **VAELoader**: `/qs/kino/backend/ComfyUI/nodes.py:694-786`
4. **CLIPLoader**: `/qs/kino/backend/ComfyUI/nodes.py:928-953`
5. **WanImageToVideo**: `/qs/kino/backend/ComfyUI/comfy_extras/nodes_wan.py:15-60`

### Kino Bricks
1. **wan_bricks.py**: `/qs/kino/backend/bricks/wan_bricks.py`
2. **comfy_bricks.py**: `/qs/kino/backend/bricks/comfy_bricks.py`

## Следующие шаги

### Возможные улучшения
1. Добавить `DualCLIPLoader` для моделей требующих 2 CLIP
2. Реализовать `Wan22FunControlToVideo` для control video
3. Добавить `WanTrackToVideo` для траекторного контроля
4. Создать `WanSoundImageToVideo` для audio-driven генерации

### Интеграция в плагины
Можно создать Wan плагин по аналогии с SDXL:
```
plugins/
└── wan/
    ├── loader.py       # Wan plugin
    ├── README.md       # Documentation
    └── __init__.py
```

## Заключение

✅ Реализованы все 5 базовых компонентов для Wan video generation
✅ Создана полная документация (4 файла)
✅ Добавлен тестовый скрипт
✅ Обновлен основной README
✅ Все импорты работают
✅ Нет ошибок линтера

**Статус: Готово к использованию!** 🎉

