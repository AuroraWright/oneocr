Originally from: https://b1tg.github.io/post/win11-oneocr/ and https://github.com/Cecilia-pj/win11_oneocr_py. Webserver code from https://github.com/GitHub30/winocr .
Basic library which returns a dict with the text, text angle, lines, and words in each line (with text, bounding boxes and confidence values for each word) using the Snipping Tool OCR on Windows. It also includes a small web server to serve OCR requests, as inspired by WinOCR.

To use you need to place 3 files from recent Windows 11 versions of Snipping Tool. The easiest way to get them is through https://store.rg-adguard.net, insert "https://apps.microsoft.com/detail/9mz95kl8mr0l" in the search box and download the most recent "Microsoft.ScreenSketch" "msixbundle" file. Then rename it to .zip and extract it. Extract the "SnippingToolApp" "msix" file for your architecture (x64 or ARM64) again after also renaming it to .zip, and the files should be in the "SnippingTool" folder.

- oneocr.dll
- oneocr.onemodel
- onnxruntime.dll

These files should be placed in the C:/Users/your_user_folder/.config/oneocr folder.

Usage is similar to WinOCR:

```py
from PIL import Image
import oneocr

img = Image.open('test.jpg')
model = oneocr.OcrEngine()
model.recognize_pil(img)['text']
```

```py
import requests

bytes = open('test.jpg', 'rb').read()
requests.post('http://localhost:8001/', bytes).json()['text']
```

```py
import cv2
import oneocr

img = cv2.imread('test.jpg')
model = oneocr.OcrEngine()
model.recognize_cv2(img)['text']
```

To run the server:
```
pip install oneocr[api]
oneocr_serve
```

The returned dict looks like this:
```py
{'text': '(Press CTRL+C to quit)', 'text_angle': 0.06437717378139496, 'lines': [{'text': '(Press CTRL+C to quit)', 'bounding_rect': {'x1': 13.0, 'y1': 38.0, 'x2': 458.0, 'y2': 38.0, 'x3': 458.0, 'y3': 77.0, 'x4': 13.0, 'y4': 76.0}, 'words': [{'text': '(Press', 'bounding_rect': {'x1': 14.353108406066895, 'y1': 39.69878387451172, 'x2': 140.3456573486328, 'y2': 41.31085205078125, 'x3': 139.93304443359375, 'y3': 73.41635131835938, 'x4': 13.778392791748047, 'y4': 74.0859375}, 'confidence': 0.9870722889900208}, {'text': 'CTRL+C', 'bounding_rect': {'x1': 155.53341674804688, 'y1': 41.37630844116211, 'x2': 273.66094970703125, 'y2': 41.40755081176758, 'x3': 273.42254638671875, 'y3': 74.35794830322266, 'x4': 155.1415557861328, 'y4': 73.46490478515625}, 'confidence': 0.9822005033493042}, {'text': 'to', 'bounding_rect': {'x1': 298.973388671875, 'y1': 41.21086502075195, 'x2': 334.41058349609375, 'y2': 40.91863250732422, 'x3': 334.25103759765625, 'y3': 75.33767700195312, 'x4': 298.7672424316406, 'y4': 74.74362182617188}, 'confidence': 0.9981738328933716}, {'text': 'quit)', 'bounding_rect': {'x1': 357.4715881347656, 'y1': 40.60407257080078, 'x2': 459.0, 'y2': 38.89320755004883, 'x3': 459.0, 'y3': 78.0, 'x4': 357.3414306640625, 'y4': 75.82363891601562}, 'confidence': 0.9932758808135986}]}]}
```
