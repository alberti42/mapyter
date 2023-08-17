# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from mapyter._MagicPosix import MagicPosix, option, magic_usage
from IPython.display import HTML

class HTMLMagic(MagicPosix):
	
	@magic_usage('%%html [-h] HTML')
	@option("HTML", nargs="+", action="store", help='HTML content to display')
	def line_html(self,line,code,**kwargs):
		"""
Display the content of the line as HTML.

Example:

  %html <u>This is underlined!</u>
"""
		html = HTML(line)
		self.kernel.Display(html)
		
		
	def cell_html(self,line,code,**kwargs):
		"""
Display contents of the cell as HTML.

Example:

  %%html 

  <script src="..."></script>

  <div>Contents of div tag</div>
"""
		html = HTML(code)
		self.kernel.Display(html)
		self.evaluate = False
		
		
def register_magics(kernel):
	kernel.register_magics(HTMLMagic)
