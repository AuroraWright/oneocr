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
{'text': '(Press CTRL+C to quit)', 'text_angle': 0.1287536919116974, 'lines': [{'text': '(Press CTRL+C to quit)', 'bounding_rect': {'x1': 15.0, 'y1': 55.0, 'x2': 460.0, 'y2': 55.0}, 'words': [{'text': '(Press', 'bounding_rect': {'x1': 16.31104850769043, 'y1': 56.61604309082031, 'x2': 144.23599243164062, 'y2': 58.337398529052734}, 'confidence': 0.9861753582954407}, {'text': 'CTRL+C', 'bounding_rect': {'x1': 158.8894805908203, 'y1': 58.3936767578125, 'x2': 278.3717956542969, 'y2': 58.33317565917969}, 'confidence': 0.9664466381072998}, {'text': 'to', 'bounding_rect': {'x1': 301.47845458984375, 'y1': 58.12306213378906, 'x2': 339.2376403808594, 'y2': 57.741416931152344}, 'confidence': 0.9981067776679993}, {'text': 'quit)', 'bounding_rect': {'x1': 362.3424377441406, 'y1': 57.38189697265625, 'x2': 461.0, 'y2': 55.520843505859375}, 'confidence': 0.9936797022819519}]}]}
```
