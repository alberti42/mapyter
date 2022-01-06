import contextlib
import subprocess
import os
import json
import base64
import IPython.display as disp
import traceback
import glob

from mapyter._DiaryPipe import DOWNLOAD_BTN_TAG

@contextlib.contextmanager
def chdir(newdir):
    olddir = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(olddir)
        
def createAnimations(kernel,savedir,settings):
    fmt = settings['video_format']
    
    if settings['exporter'] == 'export_fig':
        # we skip antialias since export_fig takes care of it
        settings['antialias'] = 1
        
    with chdir(savedir):
        for theId, v in kernel._figs.items():
            html = DOWNLOAD_BTN_TAG.format(fmt=fmt)
            if v['count'] > 1:
                if fmt in ('mp4','mov'):
                    video_name = 'mov{num:03d}.{fmt:s}'.format(num=v['num'],fmt=fmt)
                    # H264 encoder requires the final size to be divisible by 2; we thus we crop one pixel if necessary
                    if fmt == 'mov':
                        codec =  ['prores_ks','-profile:v','4']
                    elif fmt == 'mp4':
                        codec =  ['h264', '-pix_fmt', 'yuv420p']
                    
                    ffmpeg_cmd = ['ffmpeg','-f','image2','-r','{fps:1.3f}'.format(fps=settings['fps_eval']),'-loglevel','error', \
                        '-i','img{num:03d}_%03d.png'.format(num=v['num']),'-filter_complex', \
                        '[0] crop=w=floor(in_w/2)*2:h=floor(in_h/2)*2', '-y', '-vcodec'] + codec + [video_name]
                    # kernel.Print(" ".join(ffmpeg_cmd))
                    try:
                        ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    except FileNotFoundError:
                        kernel.Error("Error: 'ffmpeg' could not be found in the path. Failed to produce .{fmt:s} animation.".format(fmt=fmt));
                        break
                    except Exception as ex:
                        tb = ex.__traceback__
                        kernel.Error("Traceback (most recent call last):\n"+"".join(traceback.format_tb(tb)).rstrip('\n'))
                        break

                    _, stderr = ffmpeg.communicate()
    
                    if ffmpeg.returncode != 0:
                        kernel.Error("Error: 'ffmpeg' failed to produce .{fmt:s} animation for figure number {num:d} with message:\n".format(fmt=fmt,num=v['num']))
                        kernel.Error(stderr.decode('utf_8'))
                        break
                
                elif fmt in ('zip'):
                    zip_name = 'mov{num:03d}.{fmt:s}'.format(num=v['num'],fmt=fmt)
                    img_list = glob.glob('img{num:03d}_*'.format(num=v['num']))
                    zip_cmd = ['zip','-r',zip_name] + img_list
                    try:
                        zip_pkg = subprocess.Popen(zip_cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    except FileNotFoundError:
                        kernel.Error("Error: 'zip' could not be found in the path. Failed to produce .{fmt:s} package.".format(fmt=fmt));
                        break
                    except Exception as ex:
                        tb = ex.__traceback__
                        kernel.Error("Traceback (most recent call last):\n"+"".join(traceback.format_tb(tb)).rstrip('\n'))
                        break

                    stdout, _ = zip_pkg.communicate()

                    if zip_pkg.returncode != 0:
                        kernel.Error("Error: 'zip' failed to produce .{fmt:s} package for figure number {num:d} with message:\n".format(fmt=fmt,num=v['num']))
                        kernel.Error(stdout.decode('utf_8'))
                        break

                    with open(zip_name, 'rb') as f:
                        video = "data:application/{fmt:s};base64,".format(fmt=fmt)+base64.encodebytes(f.read()).decode('ascii')
        
                    # We pass the mov as mp4 because there is anyway no chance that the browser shows it for now
                    html += """<a href="{href:s}" rel="MATLAB animation in .{fmt:s} package" download="matlab_graph.{fmt:s}" target="_blank"><i style="font-size: 30px; margin: 10px; color: black;" class="fas fa-file-archive"></i></a>""".format(href=video,fmt=fmt)
                    kernel.Display(disp.HTML(html),display_id=theId,update=True)

                    continue

                elif fmt in ('gif','png'):
                    video_name = 'mov{num:03d}.{fmt:s}'.format(num=v['num'],fmt=fmt)
                        
                    encoder_extra_opts = []
                    if fmt == 'png':
                        video_fmt = 'apng'
                        encoder_extra_opts = ['-plays', '0']
                    elif fmt == 'gif':
                        video_fmt = 'gif'
                    
                    # alpha_threshold: sets the alpha threshold for transparency. Alpha values above this threshold will be treated as completely opaque, and values below this threshold will be treated as completely transparent. The option must be an integer value in the range [0,255]. Default is 128.
                    filters = """[0] split [o1][o2]; [o1] palettegen=stats_mode=full [palette];""" \
                              """[o2][palette] paletteuse=dither=none:diff_mode=rectangle:alpha_threshold=90"""
                                 
                    ffmpeg_cmd = ['ffmpeg','-loglevel','error','-r','{fps:1.3f}'.format(fps=settings['fps_eval']),'-f','image2', \
                                  '-i','img{num:03d}_%03d.png'.format(num=v['num']),'-f',video_fmt] + encoder_extra_opts + \
                                 ['-y', '-filter_complex', filters, video_name]
                    # kernel.Print(" ".join(ffmpeg_cmd))
                    try:
                        ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)                        
                    except FileNotFoundError:
                        kernel.Error("Error: 'ffmpeg' could not be found in the path. Failed to produce .{fmt:s} animation.".format(fmt=fmt));
                        break
                    except Exception as ex:
                        tb = ex.__traceback__
                        kernel.Error("Traceback (most recent call last):\n"+"".join(traceback.format_tb(tb)).rstrip('\n'))
                        break

                    _, stderr = ffmpeg.communicate()
                    
                    if ffmpeg.returncode != 0:
                        kernel.Error("Error: 'ffmpeg' failed to produce .{fmt:s} animation for figure number {num:d} with message:\n".format(fmt=fmt,num=v['num']))
                        kernel.Error(stderr.decode('utf_8'))
                        break

                ffprobe_cmd = ['ffprobe','-loglevel','error','-print_format','json','-show_streams',video_name]
                try:
                    ffprobe = subprocess.Popen(ffprobe_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                except FileNotFoundError:
                    kernel.Error("Error: 'ffprobe' could not be found in the path. Failed to get info from .{fmt:s} animation.".format(fmt=fmt));
                    break
                except Exception as ex:
                    tb = ex.__traceback__
                    kernel.Error("Traceback (most recent call last):\n"+"".join(traceback.format_tb(tb)).rstrip('\n'))
                    break
        
                stdout, stderr = ffprobe.communicate()

                if ffprobe.returncode != 0:
                    kernel.Error("Error: 'ffprobe' failed to get info from the movie of figure {num:d} with message:\n".format(num=v['num']))
                    kernel.Error(stderr.decode('utf_8'))
                    break
    
                video_info = json.loads(stdout)
                # kernel.Print(video_info)
                width = video_info['streams'][0]['width']
                height = video_info['streams'][0]['height']
                
                if fmt in ('mp4'):
                    alt = """MATLAB animation. Your browser does not support the video tag."""
                    
                    with open(video_name, 'rb') as f:
                        video = "data:video/{fmt:s};base64,".format(fmt=fmt)+base64.encodebytes(f.read()).decode('ascii')
        
                    html += """<video src="{src:s}" autoplay="autoplay" controls="controls" loop="loop" width="{w:d}" height="{h:d}" class="graph-{fmt:s}">""" \
                                             """<source>{alt:s}</video>""".format(src=video,w=width,h=height,alt=alt,fmt='mp4')
                    kernel.Display(disp.HTML(html),display_id=theId,update=True)

                elif fmt in ('mov'):

                    mime = 'quicktime'

                    with open(video_name, 'rb') as f:
                        video = "data:video/{fmt:s};base64,".format(fmt=mime)+base64.encodebytes(f.read()).decode('ascii')
                    
                    html += """<a href="{href:s}" rel="{alt:s}" download target="_blank"><i style="font-size: 30px; margin: 10px; color: black;" class="fas fa-file-video"></i></a>""". \
                                format(href=video,alt="MATLAB animation in .{fmt:s} format".format(fmt=fmt))
                    kernel.Display(disp.HTML(html),display_id=theId,update=True)

                elif fmt in ('gif','png'):
                    with open(video_name, 'rb') as f:
                        video = "data:image/{fmt:s};base64,".format(fmt=fmt)+base64.encodebytes(f.read()).decode('ascii')
        
                    html += """<img src="{src:s}" alt="Matlab animation" width="{w:d}" height="{h:d}" class="graph-{fmt:s}">""". \
                            format(src=video,w=width,h=height,fmt=fmt)
                    kernel.Display(disp.HTML(html),display_id=theId,update=True)
                    
            