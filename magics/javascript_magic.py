# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from mapyter._MagicPosix import MagicPosix, option, magic_usage
from IPython.display import Javascript

class JavascriptMagic(MagicPosix):

    @magic_usage('%%html [-h] JAVASCRIPT')
    @option("JAVASCRIPT", nargs="+", action="store", help='JAVASCRIPT content to execute')
    def line_javascript(self,line,code,**kwargs):
        """
Execute the content of the line as JavaScript.

Example:

  %javascript alert("Hello world!")

        """
        jscode = Javascript(line)
        self.kernel.Display(jscode)

    def cell_javascript(self,line,code,**kwargs):
        """
Execute the content of the cell as JavaScript.

Example:
  
  %%javascript
  
  console.log("Display this message in the browser console!")
"""
        if code.strip():
            jscode = Javascript(code)
            self.kernel.Display(jscode)
            self.evaluate = False

def register_magics(kernel):
    kernel.register_magics(JavascriptMagic)

