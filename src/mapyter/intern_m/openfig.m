function retval = openfig(p,varargin)
    % Overwrite the built-in 'openfig' to fix figures when imported
    global Gc8i96uVM
    if Gc8i96uVM.builtin
        figout=builtin('openfig',p,varargin{:})
        if nargout
            retval = figOut;
        end
    else
        current_dir=cd(fullfile(matlabroot,'/toolbox/matlab/graphics/objectsystem/'));
        matlab.graphics.internal.figfile.FigFile(p);
        figOut=gcf();
        cd(current_dir);
        if nargout
            retval = figOut;
        end
        a_h = findobj(figOut,'Type','Axes');
        set(a_h,'LooseInset', [0.02,0.02,0.02,0.02]);
        set(figOut,...
            'InvertHardCopy','off',...
            'Color',Gc8i96uVM.color,...
            'PaperUnits','inches',...
            'Units','pixels',...
            'WindowStyle','normal',...
            'Visible',get(groot,'DefaultFigureVisible'),...
            'PaperPositionMode','manual',...
            'Position',get(groot,'DefaultFigurePosition'),...
            'PaperPosition',get(groot,'DefaultFigurePaperPosition'),...
            'ToolBar','none',...
            'Menu','none');
    end
end