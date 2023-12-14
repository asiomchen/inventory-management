from randimage import get_random_image
from matplotlib import image
import os


def generate_random_image(path: str):
    if os.path.exists(path):
        return os.path.basename(path)
    img_size = (400, 400)
    img = get_random_image(img_size)
    image.imsave(path, img)
    return os.path.basename(path)
