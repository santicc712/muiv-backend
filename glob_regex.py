from PIL import Image


# image = Image.open('static/images/photo_201037ee306a3.jpg')
# image.save('my-image.jpg.webp', 'webp', optimize=True, quality=10)
import os
import sys
from datetime import timedelta
import os
import re
import glob


def glob_re(pattern, strings):
    return list(filter(re.compile(pattern).match, strings))

# regexp = "2023-11-12"
# filenames = glob_re(r'photo_{}_(.*).jpg'.format(regexp), os.listdir("static/images/"))
# print(list(filenames))

