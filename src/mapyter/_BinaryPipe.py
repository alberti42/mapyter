import queue
import os
import errno
from json import loads as json_loads
from .tqdm_notebook import tqdm_notebook
from ._PipesHandler import _PipesHandler

class UnknownCommandError(Exception):
    def __init__(self, cmd):
        self.cmd = cmd

    def __str__(self):
        return "Received unknown command '{cmd:s}'".format(cmd=self.cmd)

class UnknownTypeError(Exception):
    def __init__(self, typ):
        self.type = typ

    def __str__(self):
        return "Type of packet '{typ:s}' unknown".format(typ=self.type)

class UnknownFormatError(Exception):
    def __init__(self, fmt):
        self.format = fmt

    def __str__(self):
        return "Image format '{fmt:s}' unknown".format(fmt=self.format)

class BinaryQueueEmptyError(Exception):
    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return "Time-out error: no binary packet received from MATLAB after {sec:d} seconds".format(sec=self.timeout)

class BinaryPipe(_PipesHandler):
    
    def __init__(self,kernel,tmpdir):
        super().__init__(kernel=kernel)
        
        self.path = os.path.join(tmpdir,'binary.pipe')
        self._q = queue.Queue()
        self.buffer = [] # buffer containing list of byte already received
        self.nbytes = 0  # bytes left to read
        self.args = {}

    def register(self):
        try:
            os.mkfifo(self.path)
        except OSError as ose: 
            if ose.errno != errno.EEXIST:
                raise
        # Open the pipe in non-blocking mode. Use read/write mode so that the pipe
        # remains opened by at least one program (namely, this thread) to avoid that POLLHUP is
        # continously thrown, see https://stackoverflow.com/a/22023610/4216175.
        # This relies on the fact that named pipes can be used duplex in contrast to anonymous pipes
        # that are unidirectional, see pipe(7) linux man page, https://linux.die.net/man/7/pipe.
        self.pipe_out = self.pipe_in = os.open(self.path, os.O_RDWR | os.O_NONBLOCK)
        
    def get_next_packet(self):
        timeout=1
        try:
            data = self._q.get(block=True,timeout=timeout)
        except queue.Empty:
            raise BinaryQueueEmptyError(timeout)
        else:
            self._q.task_done()
            return data

    def start_capture(self):
        # clear the queue from possible old packets that were not
        # received because e.g. MATLAB was interrupted by Ctrl-C
        self._q.queue.clear()
        super().start_capture()

    def signal_eof(self):
        os.write(self.pipe_in,"""{"cmd":"finished"}""".encode('utf_8') + b'\x00')
        
    def handle_packet(self,packet):
        if self._capture_evnt.isSet():
            if not self.buffer:
                retidx = packet.find(b'\x00')
                if retidx == -1:
                    self.buffer.append(packet)
                    return
            
                self.args = json_loads(packet[:retidx].decode('utf_8'))
                cmd=self.args.pop('cmd')
                if cmd == 'finished':
                    self._eof_evnt.set()
                    return
                elif cmd == 'import':
                    if self.args['type'] == 'image':
                        if self.args['format'] == 'RGB':
                            self.nbytes = self.args['width']*self.args['height']*3
                        else:
                            raise UnknownFormatError(self.args['format'])
                    else:
                        raise UnknownTypeError(self.args['type'])
                elif cmd == 'tqdm':
                    theId = self.args['id']

                    if theId in self._kernel._pbars:
                        self._kernel.Display(self._kernel._pbars[theId].get_html(n=self.args['value']),display_id=theId,update=True)
                    else:
                        pbar=tqdm_notebook(total=self.args['total'], desc=self.args['msg'],clean_after=self.args['clean'])
                        self._kernel._pbars[theId] = pbar
                        self._kernel.Display(pbar.get_html(),display_id=theId)

                else:
                    raise UnknownCommandError(cmd)
                    
                packet = packet[retidx+1:]
                if packet:
                    # process the rest of the packet, typically containing the binary part
                    self.buffer.append(b'')
                    self.handle_packet(packet)
            else:
                if self.nbytes:
                    if len(packet) >= self.nbytes:
                        self.buffer.append(packet[:self.nbytes])
                        self.args['bin'] = b''.join(self.buffer)
                        self._q.put(self.args)
                        remaining = packet[self.nbytes:]
                        self.buffer = []
                        self.nbytes = 0
                        self.args = {}
                        if remaining:
                            self.handle_packet(remaining)
                    else:
                        self.buffer.append(packet)
                        self.nbytes-=len(packet)
                else:     
                    buffer = self.buffer[0] + packet
                    self.buffer = []
                    self.handle_packet(buffer)
                return
