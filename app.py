import os
from flask import Flask, request, make_response
from urllib import urlopen
from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageStat
from StringIO import StringIO

app = Flask(__name__)
app.debug = bool(os.environ.get('DEBUG', False))

@app.route('/')
def filter():
    if 'url' in request.args:
        url = request.args.get('url')
        filter = request.args.get('op')
        args = {k:request.args[k] for k in request.args if k not in ('url', 'op')}
        img = Image.open(StringIO(urlopen(url).read()))
        return image_response(img, filter, args)
    else:
        return 'pass an image as ?url='

def image_response(img, op, args):
    result = CONVERT.get(op, dither)(img, **args)
    out = StringIO()
    result.save(out, format='PNG')
    response = make_response(out.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

def dither(img, **kwargs):
    return img.convert('1')

def threshold(img, **kwargs):
    level = int(kwargs.get('level', 128))
    return img.convert('L').point(lambda p: 255 if p > level else 0)

def edge(img, **kwargs):
    return threshold(img.convert('L').filter(ImageFilter.EDGE_ENHANCE), **kwargs)

def edge_more(img, **kwargs):
    return threshold(img.convert('L').filter(ImageFilter.EDGE_ENHANCE_MORE), **kwargs)

def avg_filter(filter):
    def func(img, **kwargs):
        size = int(kwargs.get('size', 3))
        if size % 2 != 1:
            size = 3
        return threshold(img.convert('L').filter(filter(size)), **kwargs)
    return func

def rank(img, **kwargs):
    size, rank = kwargs.get('size', 3), kwargs.get('rank', 5)
    rf = ImageFilter.RankFilter(int(size), int(rank))
    return threshold(img.convert('L').filter(rf), **kwargs)

def equalize(img, **kwargs):
    return ImageOps.equalize(img.convert('L')).convert('1')

#def halftone(img, **kwargs):
#    img = ImageOps.autocontrast(img.convert('L'))
#    w, h = img.size
#    ht_img = Image.new('1', (w,h), 1)
#    for x in range(0, w-5, 5):
#        for y in range(0, h-5, 5):
#            t = sum([img.getpixel((px,py)) for px in range(x, x+5) for py in range(y, y+5)])/25
#            ht_pixel(ht_img, x+2, y+2, t)
#    return ht_img

def halftone(im, sample=10, scale=1):
    sample, scale = int(sample), int(scale)
    dots = []
    size = im.size[0]*scale, im.size[1]*scale
    half_tone = Image.new('L', size, 255)
    draw = ImageDraw.Draw(half_tone)
    for x in xrange(0, im.size[0], sample):
        for y in xrange(0, im.size[1], sample):
            box = im.crop((x, y, x + sample, y + sample))
            stat = ImageStat.Stat(box)
            diameter = ((255 - stat.mean[0]) / 255)**0.5
            edge = 0.5*(1-diameter)
            x_pos, y_pos = (x+edge)*scale, (y+edge)*scale
            box_edge = sample*diameter*scale
            draw.ellipse((x_pos, y_pos, x_pos + box_edge, y_pos + box_edge), fill=0)
    #half_tone = half_tone.rotate(-angle, expand=1)
    width_half, height_half = half_tone.size
    xx=(width_half-im.size[0]*scale) / 2
    yy=(height_half-im.size[1]*scale) / 2
    half_tone = half_tone.crop((xx, yy, xx + im.size[0]*scale, yy + im.size[1]*scale))
    dots.append(half_tone)
    return Image.merge('L', dots)

def testwalk(img, **kwargs):
    #img = ImageOps.autocontrast(img.convert('L'))
    w, h = img.size
    ht_img = Image.new('1', (w,h), 1)
    for x in range(0, w-5, 5):
        for y in range(0, h-5, 5):
            ht_img.putpixel((x+2, y+2), (255, 0, 0))
    return ht_img

pixelmaps = [
    [
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
    ],
    [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
    ],
    [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
]
def ht_pixel(img, x, y, i):
    map = pixelmaps[i/255]
    for px, row in enumerate(map):
        for py, p in enumerate(row):
            img.putpixel((x+px, y+py), p)

CONVERT = {
    'dither': dither,
    'threshold': threshold,
    'edge': edge,
    'edge-more': edge_more,
    'min': avg_filter(ImageFilter.MinFilter),
    'median': avg_filter(ImageFilter.MedianFilter),
    'max': avg_filter(ImageFilter.MaxFilter),
    'mode': avg_filter(ImageFilter.ModeFilter),
    'rank': rank,
    'halftone': halftone,
    'equalize': equalize,
    'testwalk': testwalk,
}

if __name__ == '__main__':
   # Bind to PORT if defined, otherwise default to 5000.
   port = int(os.environ.get('PORT', 5000))
   app.run(host='0.0.0.0', port=port)
