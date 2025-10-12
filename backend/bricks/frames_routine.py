from PIL import Image, ImageOps, ImageSequence
import numpy as np

from config import Config

def save_frame(project_name: str, frame_id: int, images, filename_prefix="frame", compress_level=0):

    result = []
    for (batch_number, image) in enumerate(images):
        img_id = frame_id + batch_number
        full_filename_path = f"{Config.PROJECTS_DIR}/{project_name}/frames/{filename_prefix}_{img_id}.png"

        i = 255. * image.cpu().detach().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        img.save(full_filename_path, compress_level=compress_level)
        result += [full_filename_path]

    return result
