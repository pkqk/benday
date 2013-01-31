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

def halftone(img, sample=10):
    # taken from: https://github.com/philgyford/python-halftone
    im = ImageOps.autocontrast(img.convert('L'))
    sample = int(sample)
    result = Image.new('L', im.size, 255)
    draw = ImageDraw.Draw(result)
    for x in xrange(0, im.size[0], sample):
        for y in xrange(0, im.size[1], sample):
            box = im.crop((x, y, x + sample, y + sample))
            stat = ImageStat.Stat(box)
            diameter = ((255 - stat.mean[0]) / 255)**0.5
            edge = 0.5*(1-diameter)
            x_pos, y_pos = (x+edge), (y+edge)
            box_edge = sample*diameter
            draw.ellipse((x_pos, y_pos, x_pos + box_edge, y_pos + box_edge), fill=0)
    return result

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
}

if __name__ == '__main__':
   # Bind to PORT if defined, otherwise default to 5000.
   port = int(os.environ.get('PORT', 5000))
   app.run(host='0.0.0.0', port=port)
