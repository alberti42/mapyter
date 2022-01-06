import io
import os
from PIL import Image
from json import loads as json_loads
import IPython.display as disp
import base64
from xml.dom import minidom
import re
from hashlib import md5
from fcntl import fcntl, F_GETFL, F_SETFL
from ._PipesHandler import _PipesHandler, STDOUT, STDERR, WrongHashError
try:
    from matlab.engine import MatlabExecutionError, EngineError
except:
    class MatlabExecutionError(Exception): pass
    class EngineError(Exception): pass

DOWNLOAD_BTN_TAG = """<button onclick="window.download_matlab_fig(this,'{fmt:s}');" class="jupyter-widgets jupyter-button widget-button" style="height: auto; """ \
                   """width: auto; padding: 5px 10px 5px 15px; position: absolute; top: 0px; right: 0px;">""" \
                   """<i class="fa-save fa"></i></button>"""

ORANGE = '\x1b[38;2;255;100;0m'
NORMAL = '\x1b[0m'

class DiaryPipe(_PipesHandler):
    def __init__(self,kernel,fileno):
        super().__init__(kernel=kernel)

        self._fileno = fileno
        self._always_capture = False
        self._eof_evnt_intern = False
        self._blks_meta = []
        self.buffer = ""
        self._fd_orig = None

        self.re_error = ((re.compile(r"(?<=Error in ).*?Gc8i96uVM_(?:code|post)(.*?\(line )(\d+)(.*?)\n",re.MULTILINE),self.matlab_error_repl1),
                         (re.compile(r"(?<=Error: )File: .*?Gc8i96uVM_(?:code|post).m(.*?)Line: (\d+)(.*?)\n"),self.matlab_error_repl2),
                         (re.compile(r"(^Unable to find function.*?within).*?Gc8i96uVM_code.m"),r"\g<1> Jupyter cell"),
                         (re.compile(r"(^Output argument.*?)Gc8i96uVM_code"),r"\g<1>Jupyter cell"),)
        self.re_warning_blk = re.compile(r"^(Warning: .*?)(\n> )((?:In .*?\n)+)",re.MULTILINE)
        self.re_warning = re.compile(r"In Gc8i96uVM_(?:code|post)(?:.m)?(.*?\(line )(\d+)(.*?)\n",re.MULTILINE)
        
        if fileno == STDOUT:
            self._handler = self._processStdout
            self.settings = {}
        elif fileno == STDERR:
            self._handler = self._processStderr
            self._always_capture = True

    def signal_eof(self):
        # MATLAB does not allow the user to write \x00 byte on stdout
        # so we can use this byte to signal the end of transmission
        os.write(self.pipe_in,b'\x00')
                
    def register(self):
        self._fd_orig = os.dup(self._fileno)
        pipe_out, pipe_in = os.pipe()
        os.dup2(pipe_in,self._fileno)
        fcntl(pipe_out,F_SETFL,fcntl(pipe_out,F_GETFL)|os.O_NONBLOCK)
        self.pipe_out = pipe_out
        self.pipe_in = pipe_in

    def unregister(self):
        if self._fd_orig:
            # Restore the file descriptor when it terminates and the original one was properly stored
            os.dup2(self._fd_orig,self._fileno)

    def handle_packet(self,packet):
        # check at the end of the buffer the presence of the termination byte \x00
        if packet[-1] == 0:
            # take note of the termination signal
            self._eof_evnt_intern = True
            packet = packet[:-1]
        
        # process the buffer
        if packet and (self._always_capture or self._capture_evnt.isSet()):
            self._handler(packet.decode('utf_8'))

        # signal that it is finished in case of \x00 termination
        if self._eof_evnt_intern:
            # process what is left on the buffer
            if self.buffer:
                buffer = self.buffer
                self.buffer = ""
                self._handler(buffer)
            
            self._eof_evnt.set()

    def matlab_error_tokens(self,m):
        l = int(m.group(2))
        l_remapped = '<undetermined>'
        tot = 0
        for blk in self._blks_meta:
            tot += blk['lines']
            if l<=tot:
                l_remapped = "{:d}".format(l-tot+blk['lines']+blk['offset'])
                break
        return (blk['name'], m.group(1), l_remapped, m.group(3))

    def matlab_error_repl1(self,m):
        tokens = self.matlab_error_tokens(m)
        return "Jupyter " + tokens[0] + tokens[1] + tokens[2] + tokens[3] + "\n"

    def matlab_error_repl2(self,m):
        tokens = self.matlab_error_tokens(m)
        return "Jupyter " + tokens[0] +  tokens[1] + "(Line:" + tokens[2] + tokens[3] + ")\n"

    def matlab_warning_repl(self,text):
        split = self.re_warning_blk.split(text,maxsplit=1)
        if len(split) == 1:
            return split[0]
        else:
            msg = (split[1], split[2] + "In " + self.re_warning.sub(self.matlab_error_repl1,split[3]))
            if self._kernel._warnings:
                if self._kernel._warnings['group']:
                    warn_hash = md5(split[3].encode('utf_8')).hexdigest()
                else:
                    warn_hash = md5((split[1]+split[3]).encode('utf_8')).hexdigest()
                if warn_hash in self._kernel._warnings_log:
                    self._kernel._warnings_log[warn_hash]['count']+=1
                else:
                    self._kernel._warnings_log[warn_hash] = {'msg':msg,'count':1}

                if self._kernel._warnings_log[warn_hash]['count'] > self._kernel._warnings['max_num']:
                    if self._kernel._warnings['log']:
                        self._kernel.log.warning(msg[0] + msg[1].rstrip('\n'))
                    msg_txt = ''
                else:
                    msg_txt = ORANGE + msg[0] + msg[1] + NORMAL
            else:
                msg_txt = ORANGE + msg[0] + msg[1] + NORMAL
            
            return split[0] + msg_txt + self.matlab_warning_repl(split[4])

    def _processWarnings(self,text):
        self._kernel.Write(self.matlab_warning_repl(text))

    def _processStderr(self,text):
        for regex,fct in self.re_error:
            text = regex.sub(fct, text)

        self._kernel.Error(text,end="")

    def _processStdout(self, text):
        if not self.buffer:
            keyidx = text.find('[Gc8i96uVM,')
            if keyidx == -1:
                # in case there is no command
                self._processWarnings(text)
                return
            else:
                if keyidx>0:
                    # take care of text before command
                    self._processWarnings(text[0:keyidx])
                text = text[keyidx:]
                retidx = text.find('\n')
                if retidx == -1:
                    # wait that the command string is completed
                    self.buffer = text
                    return
                else:
                    # process the command once completed
                    self._processCmd(text[12:],retidx-12)
                    return
                    # 12 char is to remove the magic code
        else:
            text = self.buffer + text
            self.buffer = ""
            self._processStdout(text)
            return

    def _processCmd(self, text, retidx):
        if text.startswith('import]'):
            # import time
            # time.sleep(1)
            l = len('import]: ')
            args = json_loads(text[l:retidx])
            # store in the kernel list of file names and related matlab figure number 
            theId = args['hash']
            filename = os.path.join(self._kernel.savedir,args['file'])
            fmt = self.settings['format']
            sze = (self.settings['width'],self.settings['height'])
            if fmt == "png":
                img_need_save = False
                nbytes_pipe = args['pipe_bytes']
                if nbytes_pipe:
                    # nonzero nbytes means that data are streamed through a binary pipe
                    data = self._kernel.binary_pipe.get_next_packet()

                    if data['hash'] != theId:
                        raise WrongHashError('Packet received has the wrong hash not matching the one expected for the figure.')

                    sze = sze_actual = (data['width'],data['height'])
                    image_array = data['bin']

                    # sanity check
                    if len(image_array) != nbytes_pipe:
                        # TODO: something wrong happened, an exception should be raised here
                        return
                    img=Image.frombytes(data['format'],(sze[0],sze[1]),image_array)
                    img_need_save=True
                else:
                    img=Image.open(filename)
                    # takes the effective one, since matlab might not honor the size requested
                    sze_actual=img.size
                    
                if self.settings['antialias'] != 1 and self.settings['exporter'] != 'export_fig':
                    # skip antialias for export_fig because it takes care of it
                    img=img.resize((round(sze_actual[0]/self.settings['antialias']),round(sze_actual[1]/self.settings['antialias'])))
                    sze_actual=img.size # store the new size
                    img_need_save = True
                    
                img_byte_arr=io.BytesIO()
                img.save(img_byte_arr, format='png')
                img_byte_arr=img_byte_arr.getvalue()
                if self.settings['movies'] and img_need_save:
                    with open(filename,'wb') as f:
                        f.write(img_byte_arr)
                        
                data=dict(fmt=fmt,src="data:image/png;base64," + \
                    base64.encodebytes(img_byte_arr).decode('ascii'), \
                    alt='Matlab plot',width=sze_actual[0],height=sze_actual[1])

            elif fmt == "svg":
                with open(filename,'r') as f:
                    svg=f.read() 
                svg_parse = minidom.parseString(svg)
                # Extrct svg tag, which should be at position 1
                svg_found = svg_parse.getElementsByTagName('svg')
                sze_actual=(svg_found[0].getAttribute('width'),svg_found[0].getAttribute('height'))
                svg_found[0].setAttribute('viewBox',"0,0,{w:s},{h:s}".format(w=sze_actual[0],h=sze_actual[1]))
                svg_found[0].setAttribute('width',"100%")
                svg_found[0].setAttribute('height',"100%")
                if not svg_found:
                    raise TypeError('SVG file wrongly formatted')
                data=dict(fmt=fmt,xml=svg_found[0].toxml(),width=sze[0],height=sze[1])

            # book-keeping of the figures acquired
            _figs = self._kernel._figs
            if theId in _figs:
                _figs[theId]['count']+=1
            else:
                _figs[theId] = {'num':args['num'],'count':1}

            html = DOWNLOAD_BTN_TAG.format(fmt=fmt)
            
            if fmt == "png":
                html += """<img class="graph-png" src="{src:s}" alt="Matlab plot" width="{w:d}" """ \
                                 """height="{h:d}" class="graph-png">""".format(src=data['src'],w=sze_actual[0],h=sze_actual[1])
            elif fmt == "svg":
                html += """<div class="graph-svg" style="width:{w:1.0f}px; height:{h:1.0f}px;">{xml:s}</div>""". \
                    format(xml=data['xml'],w=sze[0],h=sze[1])

            if _figs[theId]['count'] > 1:
                update = True
            else:
                update = False
            self._kernel.Display(disp.HTML(html),display_id=theId,update=update);
        elif text.startswith('clc]'):
            self._kernel.clear_output(wait=False)
                
        # take care of remaining text if something is left
        text = text[retidx+1:]
        if text:
            # important to distinguish the two cases
            if self._eof_evnt_intern:
                # in this case a signal to exit has been received all the buffer must go out,
                # assuming that all commands in the remaining buffer are entire
                self._processStdout(text)
            else:
                # in this case we have some text left, which can contain non-complete commands
                # commands must not be processed yet, and must wait that more text fills in the
                # buffer
                self.buffer = text
        
        
    