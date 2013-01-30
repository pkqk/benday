import os
from flask import Flask, request, make_response
from urllib import urlopen
from PIL import Image
from StringIO import StringIO

app = Flask(__name__)
app.debug = bool(os.environ['DEBUG'])

@app.route('/')
def filter():
    if 'url' in request.args:
        url = request.args.get('url')
        filter = request.args.get('op')
        img = Image.open(StringIO(urlopen(url).read()))
        return image_response(img, filter)
    else:
        return 'pass an image as ?url='

def image_response(img, op):
    result = CONVERT.get(op, dither)(img)
    out = StringIO()
    result.save(out, format='PNG')
    response = make_response(out.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

def dither(img, *args):
    return img.convert('1')

def threshold(img, *args):
    return img.convert('L').point(lambda p: 255 if p > 128 else 0)

CONVERT = {
    'dither': dither,
    'threshold': threshold,
}

if __name__ == '__main__':
   # Bind to PORT if defined, otherwise default to 5000.
   port = int(os.environ.get('PORT', 5000))
   app.run(host='0.0.0.0', port=port)
