import ctypes
import sys
import os
from ctypes import Structure, byref, POINTER, c_int64, c_int32, c_float, c_ubyte, c_char, c_char_p
from PIL import Image
from contextlib import contextmanager

CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'oneocr')
MODEL_NAME = 'oneocr.onemodel'
DLL_NAME = 'oneocr.dll'
MODEL_KEY = b"kj)TGtrK>f]b[Piow.gU+nC@s\"\"\"\"\"\"4"

c_int64_p = POINTER(c_int64)
c_float_p = POINTER(c_float)
c_ubyte_p = POINTER(c_ubyte)

class ImageStructure(Structure):
    '''Image data structure'''
    _fields_ = [
        ('type', c_int32),
        ('width', c_int32),      # Image width in pixels
        ('height', c_int32),     # Image height in pixels
        ('_reserved', c_int32),
        ('step_size', c_int64),  # Bytes per row
        ('data_ptr', c_ubyte_p)  # Pointer to image data
    ]

class BoundingBox(Structure):
    '''Text bounding box coordinates'''
    _fields_ = [
        ('x1', c_float),
        ('y1', c_float),
        ('x2', c_float),
        ('y2', c_float)
    ]

BoundingBox_p = POINTER(BoundingBox)

DLL_FUNCTIONS = [
    ('CreateOcrInitOptions', [c_int64_p], c_int64),
    ('OcrInitOptionsSetUseModelDelayLoad', [c_int64, c_char], c_int64),
    ('CreateOcrPipeline', [c_int64, c_int64, c_int64, c_int64_p], c_int64),
    ('CreateOcrProcessOptions', [c_int64_p], c_int64),
    ('OcrProcessOptionsSetMaxRecognitionLineCount', [c_int64, c_int64], c_int64),
    ('RunOcrPipeline', [c_int64, POINTER(ImageStructure), c_int64, c_int64_p], c_int64),

    ('GetImageAngle', [c_int64, c_float_p], c_int64),
    ('GetOcrLineCount', [c_int64, c_int64_p], c_int64),
    ('GetOcrLine', [c_int64, c_int64, c_int64_p], c_int64),
    ('GetOcrLineContent', [c_int64, POINTER(c_char_p)], c_int64),
    ('GetOcrLineBoundingBox', [c_int64, POINTER(BoundingBox_p)], c_int64),
    ('GetOcrLineWordCount', [c_int64, c_int64_p], c_int64),
    ('GetOcrWord', [c_int64, c_int64, c_int64_p], c_int64),
    ('GetOcrWordContent', [c_int64, POINTER(c_char_p)], c_int64),
    ('GetOcrWordBoundingBox', [c_int64, POINTER(BoundingBox_p)], c_int64),
    ('GetOcrWordConfidence', [c_int64, c_float_p], c_int64)
]

def bind_dll_functions(dll, functions):
    '''Dynamically bind function specifications to DLL methods'''
    for name, argtypes, restype in functions:
        try:
            func = getattr(dll, name)
            func.argtypes = argtypes
            func.restype = restype
        except AttributeError as e:
            raise RuntimeError(f'Missing DLL function: {name}') from e

try:
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    if hasattr(kernel32, 'SetDllDirectoryW'):
        kernel32.SetDllDirectoryW(CONFIG_DIR)

    dll_path = os.path.join(CONFIG_DIR, DLL_NAME)
    ocr_dll = ctypes.WinDLL(dll_path)
    bind_dll_functions(ocr_dll, DLL_FUNCTIONS)
except (OSError, RuntimeError) as e:
    sys.exit(f'DLL initialization failed: {e}')

@contextmanager
def suppress_output():
    '''Suppress stdout/stderr'''
    devnull = os.open(os.devnull, os.O_WRONLY)
    original_stdout = os.dup(1)
    original_stderr = os.dup(2)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    try:
        yield
    finally:
        os.dup2(original_stdout, 1)
        os.dup2(original_stderr, 2)
        os.close(original_stdout)
        os.close(original_stderr)
        os.close(devnull)

class OcrEngine:    
    def __init__(self):
        self._init_ocr_environment()
        self._create_pipeline()
        self._configure_processing()

    def _init_ocr_environment(self):
        '''Initialize OCR context and configuration'''
        self.ctx = c_int64()
        self._check_dll_result(
            ocr_dll.CreateOcrInitOptions(byref(self.ctx)),
            'Init options creation failed'
        )
        
        self._check_dll_result(
            ocr_dll.OcrInitOptionsSetUseModelDelayLoad(self.ctx, 0),
            'Model loading config failed'
        )

    def _create_pipeline(self):
        '''Create OCR processing pipeline'''
        model_path = os.path.join(CONFIG_DIR, MODEL_NAME)
        model_buf = ctypes.create_string_buffer(model_path.encode())
        key_buf = ctypes.create_string_buffer(MODEL_KEY)

        self.pipeline = c_int64()
        with suppress_output():
            self._check_dll_result(
                ocr_dll.CreateOcrPipeline(
                    ctypes.addressof(model_buf),
                    ctypes.addressof(key_buf),
                    self.ctx,
                    byref(self.pipeline)
                ),
                'Pipeline creation failed'
            )

    def _configure_processing(self):
        '''Configure processing parameters'''
        self.process_options = c_int64()
        self._check_dll_result(
            ocr_dll.CreateOcrProcessOptions(byref(self.process_options)),
            'Process options creation failed'
        )
        
        self._check_dll_result(
            ocr_dll.OcrProcessOptionsSetMaxRecognitionLineCount(
                self.process_options, 1000),
            'Line count config failed'
        )

    def recognize_pil(self, image):
        '''Process PIL Image object'''
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Convert to BGRA format expected by DLL
        b, g, r, a = image.split()
        bgra_image = Image.merge('RGBA', (b, g, r, a))

        return self._process_image(
            cols=bgra_image.width,
            rows=bgra_image.height,
            step=bgra_image.width * 4,
            data=bgra_image.tobytes()
        )

    def recognize_cv2(self, image_buffer):
        '''Process OpenCV image buffer'''
        import cv2

        img = cv2.imdecode(image_buffer, cv2.IMREAD_UNCHANGED)
        
        # Convert to BGRA format expected by DLL
        channels = img.shape[2] if len(img.shape) == 3 else 1
        if channels == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif channels == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

        return self._process_image(
            cols=img.shape[1],
            rows=img.shape[0],
            step=img.shape[1] * 4,
            data=img.ctypes.data
        )

    def _process_image(self, cols, rows, step, data):
        '''Common image processing logic'''
        if isinstance(data, bytes):
            data_ptr = (c_ubyte * len(data)).from_buffer_copy(data)
        else:
            data_ptr = ctypes.cast(ctypes.c_void_p(data), c_ubyte_p)
        
        img_struct = ImageStructure(
            type=3,
            width=cols,
            height=rows,
            _reserved=0,
            step_size=step,
            data_ptr=data_ptr
        )

        return self._perform_ocr(img_struct)

    def _perform_ocr(self, image_struct):
        '''Execute OCR pipeline and parse results'''
        instance = c_int64()
        self._check_dll_result(
            ocr_dll.RunOcrPipeline(
                self.pipeline,
                byref(image_struct),
                self.process_options,
                byref(instance)
            ),
            'OCR processing failed'
        )

        return self._parse_ocr_results(instance)

    def _parse_ocr_results(self, instance):
        '''Extract and format OCR results from DLL'''
        line_count = c_int64()
        self._check_dll_result(
            ocr_dll.GetOcrLineCount(instance, byref(line_count)),
            'Line count retrieval failed'
        )

        text_angle = self._get_text_angle(instance)
        lines = self._get_lines(instance, line_count)
        return {
            'text': '\n'.join(line['text'] for line in lines),
            'text_angle': text_angle,
            'lines': lines
        }

    def _get_text_angle(self, instance):
        '''Extract text angle'''
        text_angle = c_float()
        if ocr_dll.GetImageAngle(instance, byref(text_angle)) != 0:
            return 0.0
        return text_angle.value

    def _get_lines(self, instance, line_count):
        '''Extract individual text lines'''
        return [self._process_line(instance, idx) for idx in range(line_count.value)]

    def _process_line(self, instance, line_index):
        '''Process a single text line'''
        line_handle = c_int64()
        if ocr_dll.GetOcrLine(instance, line_index, byref(line_handle)) != 0:
            return {}

        return {
            'text': self._get_line_text(line_handle),
            'bounding_rect': self._get_bounding_box(line_handle, ocr_dll.GetOcrLineBoundingBox),
            'words': self._get_words(line_handle)
        }

    def _get_words(self, line_handle):
        '''Extract words from a text line'''
        word_count = c_int64()
        if ocr_dll.GetOcrLineWordCount(line_handle, byref(word_count)) != 0:
            return []

        return [self._process_word(line_handle, idx) for idx in range(word_count.value)]

    def _process_word(self, line_handle, word_index):
        '''Process individual word'''
        word_handle = c_int64()
        if ocr_dll.GetOcrWord(line_handle, word_index, byref(word_handle)) != 0:
            return {}

        return {
            'text': self._get_word_text(word_handle),
            'bounding_rect': self._get_bounding_box(word_handle, ocr_dll.GetOcrWordBoundingBox),
            'confidence': self._get_word_confidence(word_handle)
        }

    def _get_line_text(self, line_handle):
        '''Extract text content from line handle'''
        content = c_char_p()
        if ocr_dll.GetOcrLineContent(line_handle, byref(content)) == 0:
            return content.value.decode('utf-8', errors='ignore')
        return ''

    def _get_word_text(self, word_handle):
        '''Extract text content from word handle'''
        content = c_char_p()
        if ocr_dll.GetOcrWordContent(word_handle, byref(content)) == 0:
            return content.value.decode('utf-8', errors='ignore')
        return ''

    def _get_word_confidence(self, word_handle):
        '''Extract confidence value from word handle'''
        confidence = c_float()
        if ocr_dll.GetOcrWordConfidence(word_handle, byref(confidence)) == 0:
            return confidence.value
        return 0.0

    def _get_bounding_box(self, handle, bbox_function):
        '''Generic bounding box extraction'''
        bbox_ptr = BoundingBox_p()
        if bbox_function(handle, byref(bbox_ptr)) == 0 and bbox_ptr:
            bbox = bbox_ptr.contents
            return {
                'x1': bbox.x1,
                'y1': bbox.y1,
                'x2': bbox.x2,
                'y2': bbox.y2
            }
        return None

    def _check_dll_result(self, result_code, error_message):
        if result_code != 0:
            raise RuntimeError(f'{error_message} (Code: {result_code})')

def serve():
    '''Initialize and run the OCR web service'''
    import json
    import uvicorn
    from io import BytesIO
    from fastapi import FastAPI, Request, Response
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*']
    )

    ocr_processor = OcrEngine()

    @app.post('/')
    async def process_image(request: Request):
        image_data = await request.body()
        image = Image.open(BytesIO(image_data))
        result = ocr_processor.recognize_pil(image)
        return Response(
            content=json.dumps(result, indent=2, ensure_ascii=False),
            media_type='application/json'
        )

    uvicorn.run(app, host='0.0.0.0', port=8001)

if __name__ == '__main__':
    serve()