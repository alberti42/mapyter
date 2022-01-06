# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from mapyter._MagicPosix import MagicPosix, option, magic_usage
from IPython.display import Latex

class LatexMagic(MagicPosix):

    @magic_usage('%%html [-h] LATEX')
    @option("LATEX", nargs="+", action="store", help='LATEX content to render')
    def line_latex(self,line,code,**kwargs):
        """
Display the content of the line as compiled LaTeX.

Example:

  %latex $x_1 = \dfrac{a}{b}$
"""
        latex = Latex(line)
        self.kernel.Display(latex)

    def cell_latex(self,line,code,**kwargs):
        """
Display the content of the cell as compiled LaTeX.

Example:

    %%latex 

  \\begin{equation}

    i\\hbar\\frac{\\partial}{\\partial t} \\psi(x,t) = \\left [ - \\frac{\\hbar^2}{2m}\\frac{\\partial^2}{\\partial x^2} + V(x,t)\\right ] \\psi(x,t)

  \\end{equation}
        """
        latex = Latex(code)
        self.kernel.Display(latex)
        self.evaluate = False

def register_magics(kernel):
    kernel.register_magics(LatexMagic)
