# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from mapyter._MagicPosix import MagicPosix
import ipywidgets as widgets

class CloseWidgets(MagicPosix):

    def line_close_all_widgets(self,line,code,**kwargs):
        """
Close and remove all widgets from the output cells in the notebook. Note that the input cells are not affected by this operation. 
        """
   
        widgets.Widget.close_all()

def register_magics(kernel):
    kernel.register_magics(CloseWidgets)
