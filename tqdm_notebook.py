# Copyright, Andrea Alberti 2020
HTML_TAGS = ["""<div class="lm-Widget p-Widget lm-Panel p-Panel jupyter-widgets jp-OutputArea-output">
<div class="lm-Widget p-Widget lm-Panel p-Panel jupyter-widgets widget-container widget-box widget-hbox" style="display:flex;">
<div class="lm-Widget p-Widget jupyter-widgets widget-inline-hbox widget-html">
<div class="widget-html-content" style="margin-right:4px; font-family: var(--jp-code-font-family-default);">""","""%</div></div>
<div class="lm-Widget p-Widget jupyter-widgets widget-hprogress widget-inline-hbox" style="width:300px;">
<div class="progress" style="position: relative;">
<div class="progress-bar""","""" style="position: absolute; bottom: 0px; left: 0px; width:""","""%; height:100%;">
</div></div></div><div class="lm-Widget p-Widget jupyter-widgets widget-inline-hbox widget-html">
<div class="widget-html-content" style="margin-left:4px; font-family: var(--jp-code-font-family-default);">""","""</div></div></div></div>"""]

# <link href="https://use.fontawesome.com/releases/v5.0.1/css/all.css" rel="stylesheet">
# style="font-weight:900; font-family:'Font Awesome 5 Free'"
# c.SlidesExporter.font_awesome_url = 'https://use.fontawesome.com/releases/v5.0.1/css/all.css'

from IPython.display import HTML
from tqdm import tqdm
import io


class tqdm_notebook(tqdm):
    def __init__(self,*args,**kwargs):
        self.clean_after=kwargs.pop('clean_after',False)
        self.dummy_stream = io.StringIO()
        kwargs['file'] = self.dummy_stream
        super().__init__(*args,**kwargs)
        self.bar_style=""
        self.HTML = HTML(self.content())
    
    def content(self):
        format_dict = self.format_dict
        format_dict['bar_format']="{r_bar}"
        info = self.format_meter(**format_dict)
        percent=round(format_dict['n']/format_dict['total']*100)

        total = format_dict['total']
        n = format_dict['n']
        unit_scale = format_dict['unit_scale']
        elapsed = format_dict['elapsed']
        rate = format_dict['rate']
        unit = format_dict['unit']
        postfix = format_dict['postfix']
       
        # sanity check: total
        if total and n >= (total + 0.5):  # allow float imprecision (#849)
            total = None

        # apply custom scale if necessary
        if unit_scale and unit_scale not in (True, 1):
            if total:
                total *= unit_scale
            n *= unit_scale
            if rate:
                rate *= unit_scale  # by default rate = 1 / self.avg_time
            unit_scale = False

        elapsed_str = tqdm.format_interval(elapsed)

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = (n - format_dict['initial']) / elapsed
        inv_rate = 1 / rate if rate else None
        format_sizeof = tqdm.format_sizeof
        rate_noinv_fmt = ((format_sizeof(rate) if unit_scale else
                           '{0:5.2f}'.format(rate))
                          if rate else '?') + unit + '/s'
        rate_inv_fmt = ((format_sizeof(inv_rate) if unit_scale else
                         '{0:5.2f}'.format(inv_rate))
                        if inv_rate else '?') + 's/' + unit
        rate_fmt = rate_inv_fmt if inv_rate and inv_rate > 1 else rate_noinv_fmt
        
        if unit_scale:
            n_fmt = format_sizeof(n, divisor=format_dict['unit_divisor'])
            total_fmt = format_sizeof(total, divisor=format_dict['unit_divisor']) \
                if total is not None else '?'
        else:
            total_fmt = str(total) if total is not None else '?'
            n_fmt = "{n:>{width}d}".format(n=n,width=len(total_fmt)).replace(' ','&nbsp;')
        
        try:
            postfix = ', ' + postfix if postfix else ''
        except TypeError:
            pass

        remaining = (total - n) / rate if rate and total else 0
        remaining_str = tqdm.format_interval(remaining) if rate else '?'
        # try:
        #     eta_dt = datetime.now() + timedelta(seconds=remaining) \
        #         if rate and total else datetime.utcfromtimestamp(0)
        # except OverflowError:
        #     eta_dt = datetime.max

        info = '{0}/{1} [{2}&lt;{3}, {4}{5}]'.format(n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt, postfix)
        percent_txt="{:3d}".format(max(min(percent,100),0))
        return HTML_TAGS[0] + self.desc + '&nbsp;' + percent_txt + HTML_TAGS[1] + self.bar_style + HTML_TAGS[2] + percent_txt + HTML_TAGS[3] + info + HTML_TAGS[4]
    
    def get_html(self,n=None,bar_style=None):
        if n:
            self.n = n
        if bar_style:
            self.bar_style = bar_style
        content = self.content()
        self.HTML.data=content
        return self.HTML

    def close(self):
        if self.n==self.total:
            self.bar_style='-success'
        else:
            self.bar_style='-danger'
        html=self.get_html()
        super().close()
        self.dummy_stream.close()
        return html
        
"""
class tqdm_notebook_iPython(tqdm):
    def __init__(self,*args,**kwargs):
        self.clean_after=kwargs.pop('clean_after',False)
        self.dummy_stream = io.StringIO()
        kwargs['file'] = self.dummy_stream
        super().__init__(*args,**kwargs)
        self.bar_style=""
        self.HTML = HTML(self.content())
        self.handle=display(self.HTML,display_id=True)

    def content(self):
        format_dict = self.format_dict
        format_dict['bar_format']="{r_bar}"
        info = self.format_meter(**format_dict)
        percent=round(format_dict['n']/format_dict['total']*100)

        total = format_dict['total']
        n = format_dict['n']
        unit_scale = format_dict['unit_scale']
        elapsed = format_dict['elapsed']
        rate = format_dict['rate']
        initial = format_dict['initial']
        unit = format_dict['unit']
        postfix = format_dict['postfix']

        # sanity check: total
        if total and n >= (total + 0.5):  # allow float imprecision (#849)
            total = None

        # apply custom scale if necessary
        if unit_scale and unit_scale not in (True, 1):
            if total:
                total *= unit_scale
            n *= unit_scale
            if rate:
                rate *= unit_scale  # by default rate = 1 / self.avg_time
            unit_scale = False

        elapsed_str = tqdm.format_interval(elapsed)

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = (n - initial) / elapsed
        inv_rate = 1 / rate if rate else None
        format_sizeof = tqdm.format_sizeof
        rate_noinv_fmt = ((format_sizeof(rate) if unit_scale else
                           '{0:5.2f}'.format(rate))
                          if rate else '?') + unit + '/s'
        rate_inv_fmt = ((format_sizeof(inv_rate) if unit_scale else
                         '{0:5.2f}'.format(inv_rate))
                        if inv_rate else '?') + 's/' + unit
        rate_fmt = rate_inv_fmt if inv_rate and inv_rate > 1 else rate_noinv_fmt
        
        if unit_scale:
            n_fmt = format_sizeof(n, divisor=format_dict['unit_divisor'])
            total_fmt = format_sizeof(total, divisor=format_dict['unit_divisor']) \
                if total is not None else '?'
        else:
            total_fmt = str(total) if total is not None else '?'
            n_fmt = "{n:>{width}d}".format(n=n,width=len(total_fmt)).replace(' ','&nbsp;')
        
        try:
            postfix = ', ' + postfix if postfix else ''
        except TypeError:
            pass

        remaining = (total - n) / rate if rate and total else 0
        remaining_str = tqdm.format_interval(remaining) if rate else '?'
        # try:
        #     eta_dt = datetime.now() + timedelta(seconds=remaining) \
        #         if rate and total else datetime.utcfromtimestamp(0)
        # except OverflowError:
        #     eta_dt = datetime.max

        info = '{0}/{1} [{2}&lt;{3}, {4}{5}'.format(n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt, postfix)
        percent_txt="{:3d}".format(max(min(percent,100),0))
        return HTML_TAGS[0] + self.desc + '&nbsp;' + percent_txt + HTML_TAGS[1] + self.bar_style + HTML_TAGS[2] + percent_txt + HTML_TAGS[3] + info + HTML_TAGS[4]
    
    def update(self,n=None,bar_style=None):
        if n:
            self.n = n
        if bar_style:
            self.bar_style = bar_style
        content = self.content()
        self.HTML.data=content
        self.handle.update(self.HTML)

    def close(self):
        if self.n==self.total:
            self.bar_style='-success'
        else:
            self.bar_style='-danger'
        self.update()
        super().close()
        self.dummy_stream.close()
"""