from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool

class Worker(QRunnable):
    class Signals(QObject):
        finished = pyqtSignal(bool, object) 
        
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = self.Signals()
        self.setAutoDelete(True)
        
    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(True, result)
        except Exception as e:
            self.signals.finished.emit(False, str(e))