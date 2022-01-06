function drawnow(varargin)
global Gc8i96uVM
if Gc8i96uVM.builtin || ~isempty(varargin) || strcmp(Gc8i96uVM.backend,'native')
    builtin('drawnow',varargin{:});
else 
    Gc8i96uVM.builtin=true;
    if ~isempty(varargin), builtin('drawnow',varargin{:}); end
    
    c_h = gcf();
    c = c_h.Number;
    
    antialias = Gc8i96uVM.antialias;
    resolution = Gc8i96uVM.resolution;
    tmp = Gc8i96uVM.tmp;
    fmt = Gc8i96uVM.format;
    exporter = Gc8i96uVM.exporter;
    
    if ~isempty(Gc8i96uVM.newfigs)
        found = find([Gc8i96uVM.newfigs.fig]==c);
    else
        found = [];
    end
    refresh = false;
    if isempty(found)
        chars = '!#$&''()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}~';
        hash = chars(randi([1,90],1,4));
        idx = 0;
        Gc8i96uVM.newfigs = [Gc8i96uVM.newfigs,struct('fig',c,'hash',hash,'idx',idx,'lastTime',0)]; % 0 is here place holder
        found = length(Gc8i96uVM.newfigs);
        refresh=true;
    else
        hash=Gc8i96uVM.newfigs(found).hash;
        idx=Gc8i96uVM.newfigs(found).idx+1;
        Gc8i96uVM.newfigs(found).idx = idx;
        currentTime=posixtime(datetime);
        if Gc8i96uVM.movies || currentTime-Gc8i96uVM.newfigs(found).lastTime>1/Gc8i96uVM.fps
            refresh=true;
        end
    end
    if refresh
        img_name = sprintf('img%03d_%03d.%s',c,idx,fmt);
        filename=fullfile(tmp,img_name);
        nbytes_pipe=0;
        switch exporter
            case 'getframe'
                frame=frame2im(getframe(c_h));
                nbytes_pipe = numel(frame);
                fastimwrite(Gc8i96uVM.pipe,hash,permute(frame,[3,2,1]));
            case 'print'
                print(c_h,filename,sprintf('-d%s',fmt),sprintf('-r%d',round(resolution*antialias)));
            case 'exportgraphics'
                % where does the factor 4/3 come from?
                exportgraphics(c_h,filename,'Resolution',round(antialias*resolution/4*3),'BackgroundColor','w');
            case 'export_fig'
                if exist('export_fig','file')==2
                    if isempty(Gc8i96uVM.export_fig_opts), export_fig_opts = {}; else, export_fig_opts = split(Gc8i96uVM.export_fig_opts,' '); end
                    export_fig(filename,sprintf('-d%s',fmt),'-painters','-nocrop','-native',sprintf('-a%1.0f',antialias),export_fig_opts{:},c_h);
                else
                    warning('export_fig could not be found in MATLAB path. Using ''print'' exporter instead.')
                    print(c_h,filename,sprintf('-d%s',fmt),sprintf('-r%d',round(resolution*antialias)));
                end
        end
        fprintf(['[Gc8i96uVM, import]: ',jsonencode(struct('file',img_name,'hash',hash,'num',c,'pipe_bytes',nbytes_pipe)),'\n']);
        Gc8i96uVM.newfigs(found).lastTime = posixtime(datetime);
    end
    Gc8i96uVM.builtin=false;
end
end
