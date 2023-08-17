from mapyter.WrapText import wrap

import argparse
import shlex
import traceback
import sys

from contextlib import contextmanager

def unquote_arg(arg):
        if arg and arg[0] == arg[-1] and (arg[0] in ("'",'"')):
            return arg[1:-1]
        else:
            return arg

class ArgumentError(Exception):
    """An error from creating or using an argument (optional or positional).

    The string value of this exception is the message, augmented with
    information about the argument that caused it.
    """
    def __init__(self, *arguments, msg="",magic=""):
        arguments = list("/".join(args) for args in arguments)
        if len(arguments)==1:
            self.argument = "invalid argument " + arguments[0]
        elif len(arguments)>1:
            self.argument = "conflict between arguments " + " and ".join(arguments)
        self.message = msg
        self.magic = magic

    def __str__(self):
        return "%{magic:s}: {argument:s}: {message:s}".format(magic=self.magic,argument=self.argument,message=self.message)


class ArgumentParserError(Exception):
    pass

class ArgumentParserExitError(Exception):
    pass

class ArgumentParser(argparse.ArgumentParser):

    def __init__(self,*args,**kwargs):
        self.formatted_epilog = kwargs.pop('formatted_epilog','')
        super().__init__(*args,**kwargs)

    def error(self, message):
        raise ArgumentParserError("{prog:s}: {msg:s}".format(prog=self.prog,msg=message))

    def exit(self, status=0, message=''):
        raise ArgumentParserExitError(message)

    def format_help(self):
        return super().format_help() + self.formatted_epilog

Parser = ArgumentParser(add_help=True,formatter_class=lambda prog: argparse.HelpFormatter(
                    prog, indent_increment=4, max_help_position=120, width=120))

def magic_usage(msg):
    def decorator(magic_func):
        magic_func.usage = msg
        return magic_func
    return decorator
        
def option(*args, **kwargs):
    def decorator(magic_func):
        if not getattr(magic_func, 'has_options',False):
            magic_func.has_options = True
            magic_func.options = []
        magic_func.options.append({'key':args[-1].lstrip('-').replace('-','_'),'args':args,'kwargs':kwargs})
        return magic_func
    return decorator

@contextmanager
def redirected_stdout(writer):
    orig_writer = sys.stdout.write
    sys.stdout.write = writer
    try:
        yield
    finally:
        sys.stdout.write = orig_writer

class MagicPosix():
    def __init__(self, kernel):
        self.kernel = kernel
        self.evaluate = True
        self.code = ''

    def call_magic(self, mtype, name, code, line):
        self.code = code
        magic_func = getattr(self, mtype + '_' + name)
        width = 140
        try:
            epilog = getattr(magic_func,'__doc__',"")
            if epilog:
                epilog = "\nAdditional information:\n\n" + wrap(epilog.lstrip(''),width=width)
            if getattr(magic_func, 'has_options', False):
                options = magic_func.options
            else:
                options = []

            # we use the posix=False option because the only thing this option does is to preserve
            # quote characters at the beginning and end of a quoted block; it is necessary for argparse to
            # keep these blocks in quote, otherwise it becomes very error prone
            args = shlex.split(line, posix=False)
            prog = '%'+name
            usage_msg=getattr(magic_func,'usage',None)
            if usage_msg:
                usage={'usage':usage_msg}
            else:
                usage={}
            parser = ArgumentParser(prog="{prog:s}".format(prog=prog),**usage,add_help=False,formatted_epilog=epilog, \
                    description="Help describing how to use {type:s} magic {prog:s}".format(type=mtype,prog=prog), \
                    formatter_class=lambda prog: argparse.HelpFormatter(prog, indent_increment=4, max_help_position=50, width=width))
            for opt in reversed(options):
                parser.add_argument(*opt['args'],**opt['kwargs'])
            parser.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='Show this help message')
            with redirected_stdout(self.kernel.Write):
                args_parsed = vars(parser.parse_args(args))
            # safely unquote strings after argparse has done its job
            for key,val in args_parsed.items(): 
                if isinstance(val,str):
                    args_parsed[key] = unquote_arg(val)
        except ArgumentParserExitError as e:
            # don't do anything when this is empty; this happens when -h option is called and the parser must exit
            if e.args[0]:
                self.kernel.Error(str(e))
            self.evaluate = False
            return self
        except Exception as e:
            self.kernel.Error(str(e))
            self.evaluate = False
            if __debug__:
                self.kernel.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + "".join(traceback.format_tb(e.__traceback__)))
            return self

        try:
            magic_func(line,code,**args_parsed)
        except Exception as e:
            self.kernel.Error(str(e))
            self.evaluate = False
            if __debug__:
                self.kernel.Error("{:s} - Traceback (most recent call last):\n".format(type(e).__name__) + "".join(traceback.format_tb(e.__traceback__)))
        return self

    def get_magics(self, mtype):
        magics = []
        prefix = mtype + '_'
        for name in dir(self):
            if name.startswith(prefix):
                magics.append(name.replace(prefix, ''))
        return magics

    def post_process(self, retval):
        return retval
