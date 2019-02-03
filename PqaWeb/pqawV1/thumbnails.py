from io import BytesIO
from PIL import Image
import os

from .models import Target


def refresh_thumbnail(target: Target) -> None:
    image_file = BytesIO(target.image.read())
    image = Image.open(image_file)
    wo, ho = image.size  # old width and height
    wn = 640
    hn = int((ho / wo) * wn)
    image = image.resize((wn, hn), Image.ANTIALIAS)
    image_file = BytesIO()
    image = image.convert('RGB')
    image.save(image_file, 'JPEG', quality=75)
    file_name = os.path.splitext(os.path.basename(target.image.name))[0] + '_thumb.jpg'
    target.thumbnail.save(file_name, image_file, True)
