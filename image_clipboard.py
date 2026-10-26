"""Windows image clipboard with PNG alpha and a DIBV5 fallback; no dependencies."""
import ctypes,io,os,struct,time
from contextlib import contextmanager
from PIL import Image,ImageGrab,PngImagePlugin

def png_bytes(image,metadata=None):
    output=io.BytesIO();info=PngImagePlugin.PngInfo()
    if metadata:info.add_text('FellowStudio3D',metadata)
    image.convert('RGBA').save(output,format='PNG',pnginfo=info)
    return output.getvalue()

def dib_bytes(image):
    image=image.convert('RGBA');pixels=image.tobytes('raw','BGRA');header=bytearray(124)
    struct.pack_into('<IiiHHIIiiII',header,0,124,image.width,-image.height,1,32,3,len(pixels),0,0,0,0)
    struct.pack_into('<IIIII',header,40,0x00ff0000,0x0000ff00,0x000000ff,0xff000000,0x73524742)
    struct.pack_into('<I',header,108,4)
    return bytes(header)+pixels

def _api():
    if os.name!='nt':raise OSError('Image clipboard is only available on Windows.')
    from ctypes import wintypes as W
    user=ctypes.WinDLL('user32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    for name,args,result in (
        ('OpenClipboard',[W.HWND],W.BOOL),('CloseClipboard',[],W.BOOL),
        ('EmptyClipboard',[],W.BOOL),('RegisterClipboardFormatW',[W.LPCWSTR],W.UINT),
        ('SetClipboardData',[W.UINT,W.HANDLE],W.HANDLE),('GetClipboardData',[W.UINT],W.HANDLE)):
        fn=getattr(user,name);fn.argtypes=args;fn.restype=result
    for name,args,result in (
        ('GlobalAlloc',[W.UINT,ctypes.c_size_t],W.HGLOBAL),('GlobalLock',[W.HGLOBAL],ctypes.c_void_p),
        ('GlobalUnlock',[W.HGLOBAL],W.BOOL),('GlobalFree',[W.HGLOBAL],W.HGLOBAL),
        ('GlobalSize',[W.HGLOBAL],ctypes.c_size_t)):
        fn=getattr(kernel,name);fn.argtypes=args;fn.restype=result
    return user,kernel

@contextmanager
def _open(user,hwnd=None):
    for attempt in range(4):
        if user.OpenClipboard(hwnd):break
        if attempt==3:raise OSError('剪贴板正被占用，请重试。')
        time.sleep(.02)
    try:yield
    finally:user.CloseClipboard()

def copy_image(image,hwnd,metadata=None):
    user,kernel=_api();png=user.RegisterClipboardFormatW('PNG')
    if not png:raise ctypes.WinError(ctypes.get_last_error())
    blocks=[]
    try:
        for kind,data in ((png,png_bytes(image,metadata)),(17,dib_bytes(image))):
            handle=kernel.GlobalAlloc(2,len(data))
            if not handle:raise MemoryError('Could not allocate clipboard image')
            blocks.append([kind,handle]);pointer=kernel.GlobalLock(handle)
            if not pointer:raise ctypes.WinError(ctypes.get_last_error())
            try:ctypes.memmove(pointer,data,len(data))
            finally:kernel.GlobalUnlock(handle)
        with _open(user,hwnd):
            if not user.EmptyClipboard():raise ctypes.WinError(ctypes.get_last_error())
            for block in blocks:
                if not user.SetClipboardData(*block):raise ctypes.WinError(ctypes.get_last_error())
                block[1]=None
    finally:
        for _,handle in blocks:
            if handle:kernel.GlobalFree(handle)

def read_image():
    user,kernel=_api();data=None
    with _open(user):
        handle=user.GetClipboardData(user.RegisterClipboardFormatW('PNG'))
        if handle:
            size=kernel.GlobalSize(handle)
            if not 0<size<=64*1024*1024:raise ValueError('剪贴板图片过大。')
            pointer=kernel.GlobalLock(handle)
            if not pointer:raise ctypes.WinError(ctypes.get_last_error())
            try:data=ctypes.string_at(pointer,size)
            finally:kernel.GlobalUnlock(handle)
    if data is not None:
        with Image.open(io.BytesIO(data)) as image:
            image.load();return image.copy()
    image=ImageGrab.grabclipboard()
    if isinstance(image,Image.Image):return image
    if isinstance(image,list) and len(image)==1:
        with Image.open(image[0]) as source:
            if source.format!='PNG':raise ValueError('Use a PNG image')
            source.load();return source.copy()
    raise ValueError('剪贴板中没有图片，请先复制一张 UV 贴图。')
