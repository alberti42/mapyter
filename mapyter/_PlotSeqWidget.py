import ipywidgets as widgets
from traitlets import Unicode,Dict

# This module is no longer used.

# See js/lib/example.js for the frontend counterpart to this file.

# def img_to_json(value, widget):
#     return value
#
# def img_from_json(value, widget):
#     print(value)
#     return value

@widgets.register
class PlotSeqWidget(widgets.DOMWidget):

    # Name of the widget view class in front-end
    _view_name = Unicode('PlotSeqView').tag(sync=True)

    # Name of the widget model class in front-end
    _model_name = Unicode('PlotSeqModel').tag(sync=True)

    # Name of the front-end module containing widget view
    _view_module = Unicode('jupyter-widget-plotseq').tag(sync=True)

    # Name of the front-end module containing widget model
    _model_module = Unicode('jupyter-widget-plotseq').tag(sync=True)
 
    # Version of the front-end module containing widget view
    _view_module_version = Unicode('0.1.0').tag(sync=True)
    # Version of the front-end module containing widget model
    _model_module_version = Unicode('0.1.0').tag(sync=True)
    
    # Widget properties are defined as traitlets. Any property tagged with `sync=True`
    # is automatically synced to the frontend *any* time it changes in Python.
    # It is synced back to Python from the frontend *any* time the model is touched.
    data = Dict(default_value={}).tag(sync=True)
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        #self.layout.width = 'auto'
        #self.layout.height = 'auto'
        self.on_msg(self.handle_messages)

    def close_including_layout(self):
        self.layout.close()
        self.close()

    def handle_messages(self, _, content, buffers):
        # the omitted argument would be the entire widget with the whole data in it
        if content.get('event', '') == 'close_widget':
            self.close_including_layout()
