"""macOS UI watchdog: record stacks on a stalled event loop, never call Tk off-thread."""
import faulthandler
import platform
import sys
import traceback
from pathlib import Path


class Watchdog:
    def __init__(self, root):
        self.root=root;self.job=None;self.closed=False
        path=Path(root.state_path).parent/'runtime-diagnostics.log'
        if path.exists():path.replace(path.with_name('runtime-diagnostics.previous.log'))
        self.stream=path.open('w',encoding='utf-8')
        self.stream.write(f'Python {sys.version}\nPlatform {platform.platform()}\n')
        self.stream.write(f'Tcl {root.tk.call("info","patchlevel")} Tk {root.tk.call("package","provide","Tk")}\n')
        self.stream.write('If the Tk event loop stalls for 15 seconds, all Python thread stacks follow.\n')
        self.stream.flush()
        self.previous=root.report_callback_exception
        root.report_callback_exception=self.exception
        self.pulse()

    def pulse(self):
        if self.closed:return
        # The native watchdog writes once per stall. Rearm only on the UI thread.
        faulthandler.dump_traceback_later(15,file=self.stream,repeat=False)
        self.job=self.root.after(2000,self.pulse)

    def exception(self,*args):
        traceback.print_exception(*args,file=self.stream);self.stream.flush()
        self.previous(*args)

    def close(self):
        if self.closed:return
        self.closed=True
        faulthandler.cancel_dump_traceback_later()
        if self.job:
            try:self.root.after_cancel(self.job)
            except Exception:pass
        self.root.report_callback_exception=self.previous
        self.stream.close()


def install(root):
    if sys.platform!='darwin':return None
    try:return Watchdog(root)
    except (OSError,RuntimeError):return None
