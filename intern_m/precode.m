global Gc8i96uVM;
Gc8i96uVM=struct('tmp','{tmpdir:s}','backend','{backend:s}','format','{fmt:s}',...
    'resolution',{res:1.0f},'antialias',{antialias:1.0f},'movies',{movies:s},...
    'fps',{fps:1.3f},'exporter','{exporter:s}','export_fig_opts','{export_fig_opts:s}',...
    'newfigs',struct([]),'pipe','{binary_pipe:s}','builtin',false);
% where does 4/3 factor come from?
if strcmp(Gc8i96uVM.format,'svg'),Gc8i96uVM.svg_fix=4/3/{rescaling:1.3f};Gc8i96uVM.antialias=1;else Gc8i96uVM.svg_fix=1;end
if strcmp(Gc8i96uVM.exporter,'getframe'),Gc8i96uVM.alias_fix=Gc8i96uVM.antialias;else Gc8i96uVM.alias_fix=1;end
if strcmp(Gc8i96uVM.format,'svg'),Gc8i96uVM.color='None';else,Gc8i96uVM.color='w';end
set(groot,...
    'DefaultFigureRenderer','painters',...
    'DefaultFigureInvertHardCopy','off',...
    'DefaultFigureColor',Gc8i96uVM.color,...
    'DefaultAxesLooseInset', [0.02,0.02,0.02,0.02],...
    'DefaultFigurePaperUnits','inches',...
    'DefaultFigureUnits','pixels',...
    'DefaultFigureWindowStyle','normal',...
    'DefaultFigureVisible','{visible:s}',...
    'DefaultFigurePaperPositionMode','manual',...
    'DefaultFigurePosition',[0,0,{width:1.0f},{height:1.0f}]*Gc8i96uVM.alias_fix,...
    'DefaultFigurePaperPosition',Gc8i96uVM.svg_fix*[0,0,{width:1.0f}, {height:1.0f}]/{res:1.0f},...
    'DefaultFigureToolBar','none',...
    'DefaultFigureMenu','none');
builtin('clear','Gc8i96uVM'); % hide it from base workspace