import os
from flask import Flask, request, make_response
from urllib import urlopen
from PIL import Image, ImageFilter
from StringIO import StringIO

app = Flask(__name__)
app.debug = bool(os.environ['DEBUG'])

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
}

if __name__ == '__main__':
   # Bind to PORT if defined, otherwise default to 5000.
   port = int(os.environ.get('PORT', 5000))
   app.run(host='0.0.0.0', port=port)
