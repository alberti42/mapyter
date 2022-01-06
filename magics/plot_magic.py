# Copyright (c) Andrea Alberti, 2020

from mapyter._MagicPosix import MagicPosix, option, ArgumentError

from mapyter.helper_fcnts import validatestring, InvalidStringError

import re



format_opt = ("-f","--format")
size_arg = ('-s', '--size')
format_arg = ('-f', '--format')
resolution_arg = ('-r', '--resolution')
vector_rescaling_arg = ('-x', '--vector-rescaling')
exporter_arg = ('-e', '--exporter')
antialias_arg = ('-a', '--antialias')
movies_arg = ('-M', '--movies')
backend_arg = ('-b', '--backend')
as_default_arg = ('-d', '--as-default')
fps_arg = ('--fps',)
video_format_arg = ('--video-format',)
export_fig_arg = ('--export_fig',)

class ArgumentTypeError(Exception):
    """An error from trying to convert a command line string to a type."""
    pass

def parse_and_validate_options(options,defaults,init=False):

    options = {**defaults.copy(),**options.copy()}
    options.pop('as_default',None)

    # SIZE
    if init or options['size'] != defaults['size']:
        size = options['size'].split(',')
        if len(size) != 2:
            raise ArgumentError(size_arg,msg="invalid number of parameters",magic='plot')
        try:
            options['width'] = int(size[0])
        except:
            raise ArgumentError(size_arg,msg="width: must be an integer value",magic='plot')
        try:
            options['height'] = int(size[1])
        except:
            raise ArgumentError(size_arg,msg="height: must be an integer value",magic='plot')
        
    # ANTI-ALIAS
    if init or options['antialias'] != defaults['antialias']:
        if options['antialias']<1:
            raise ArgumentError(antialias_arg,msg="must be a positive integer",magic='plot')

    # VIDEO FORMAT
    if init or options['video_format'] != defaults['video_format']:
        try:
            # TODO: Include .zip package as format with individual images
            fmt = validatestring(options['video_format'],('png','apng','gif','mp4','h264','mov','prores','zip'))
            if fmt == 'apng':
                fmt = 'png'
            elif fmt == 'h264':
                fmt = 'mp4'
            elif fmt == 'prores':
                fmt = 'mov'
            options['video_format'] = fmt
        except InvalidStringError as e:
            raise ArgumentError(video_format_arg,msg=str(e).lower(),magic='plot')

    # FPS
    if init or options['fps'] != defaults['fps']:
        options['fps']=options['fps'].replace(" ","")
        if(re.sub("[^[\d/]","",options['fps'])!=options['fps']):
            raise ArgumentError(fps_arg,"invalid expression, only integer numbers and simple fractions are permitted",magic='plot')
        options['fps_eval'] = eval(options['fps'])

    # FORMAT
    if init or options['format'] != defaults['format']:
        try:
            options['format'] = validatestring(options['format'],('svg','png'))
        except InvalidStringError as e:
            raise ArgumentError(format_arg,msg=str(e).lower(),magic='plot')

    # EXPORTER
    if init or options['exporter'] != defaults['exporter']:
        try:
            options['exporter'] = validatestring(options['exporter'],('print','getframe','export_fig','exportgraphics'))
        except InvalidStringError as e:
            raise ArgumentError(exporter_arg,msg=str(e).lower(),magic='plot')

    # EXPORT_FIGS
    if init or options['export_fig'] != defaults['export_fig']:
            # remove multiple spaces, because MATLAB splits this string using an empty space delimiter
            # we don't validate it, we let MATLAB do this job
            options['export_fig']=re.sub('\ +',' ',options['export_fig'])
            
    # MOVIES
    if init or options['movies'] != defaults['movies']:
        try:
            options['movies'] = validatestring(options['movies'],('yes','no'))
        except InvalidStringError as e:
            raise ArgumentError(movies_arg,msg=str(e).lower(),magic='plot')
        else:
            options['movies'] = True if options['movies'] == 'yes' else False

    # validate possible conflict between new and old options
    if options['movies'] and options['video_format'] != 'zip' and options['format'] != 'png':
        raise ArgumentError(movies_arg,format_arg,msg="'png' image format must be selected to generate .{video_fmt:s} videos".format(video_fmt=options['video_format']),magic='plot')
    
    if options['exporter'] in ('exportgraphics','getframe','export_fig') and options['format'] != 'png':
        raise ArgumentError(exporter_arg,format_arg,msg="'png' format must be selected when '{:s}' is chosen as exporter".format(options['exporter']),magic='plot')
        
    return options

class PlotMagic(MagicPosix):

    def get_default_options(self):
        default_options = {}
        for opt in self.line_plot.options:
            if 'default' in opt['kwargs']:
                default_options[opt['key']] = opt['kwargs']['default']
        return default_options

    def set_default_options(self,default_options):
        line_plot_options=self.line_plot.options
        for opt in line_plot_options:
            opt['kwargs']['default']=default_options[opt['key']]
        
    @option(*size_arg, action='store', metavar='width,height', default="600,400", type=str, help='Pixel size of plots (default: %(default)s)')
    @option(*format_arg, action='store', type=str, metavar='{svg,png}', default="svg", help='Plot format (default: %(default)s)')
    @option(*resolution_arg, action='store', metavar='FACTOR', default=96, type=int, help='Resolution FACTOR in pixels per inch; not relevant for vector graphics (default: %(default)s)')
    @option(*vector_rescaling_arg, action='store', metavar='FACTOR', default=1, type=float, help='Vector-graphics rescaling FACTOR; only relevant for vector graphics (default: %(default)s)')
    @option(*exporter_arg, action='store', type=str, metavar='TYPE', default='print', help='Exporter TYPE chosen among {print,getframe,export_fig,exportgraphics} (default: %(default)s)')
    @option(*antialias_arg, action='store', type=int, metavar='FACTOR', default=1, help='Anti-aliasing FACTOR; not relevant for vector graphics (default: %(default)s)')
    @option(*movies_arg, action='store', type=str, metavar='{yes,no}', default='no', help='Create movies for sequences of plots in the same figure (default: %(default)s)')
    @option(*backend_arg, action='store', type=str, metavar='TYPE', default='inline', help='Backend TYPE: {\"inline\",\"native\"} (default: %(default)s)')
    @option(*as_default_arg, action='store_true', help='When selected, set the current values as default')
    @option(*fps_arg, action='store', type=str, metavar='FPS', default='30', help='Frame rate FPS in Hz; fractions (e.g. 1/3) are accepted (default: %(default)s)')
    @option(*video_format_arg, action='store', metavar='FMT', default='gif', type=str,help='Video format FMT chosen among {png|apng,gif,mp4|h264,mov|prores} (default: %(default)s)')
    @option(*export_fig_arg, action='store', metavar='OPTIONS', default="''", type=str, help="Extra OPTIONS provided to export_fig when selected as exporter (default: %(default)s)")
    def line_plot(self,line,code,**options):
        """
This magic configures MATLAB plotting for the cell. With the backend 'inline', plots are
displayed in Jupyter, while with 'native' plots are shown in MATLAB if this runs with graphical interface. Also to note that
FPS specifies the frame rate for the video, but also determines the highest refresh rate of plots when refreshing plots for live animations.
Final remark, the option --as-default has effect on plots in other cells as it redefines the default parameters.

Examples:

  %plot inline -r96 -a2 -s 800,800 -fpng --exporter getframe -Myes --fps 4 --video-format mp4 --export_fig-opts ""
""" 
        self.kernel._current_plot_settings = parse_and_validate_options(options,self.kernel._default_plot_settings)
        
        if options.get('as_default',False):
            options['as_default'] = False
            self.set_default_options(options)
            self.kernel._default_plot_settings = self.kernel._current_plot_settings

        self.evaluate = True
        
def register_magics(kernel):
    kernel.register_magics(PlotMagic)
    plot_magic=kernel.line_magics['plot']
    kernel._default_plot_settings = parse_and_validate_options(plot_magic.get_default_options(),plot_magic.get_default_options(),init=True)
