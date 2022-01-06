function ret = figure(varargin)
    % Overwrite the built-in 'figure' to allow one to create
    % a new figure with the specified number and attributes
    % Importantly, it also bypass 'figure' behavior displaying the figure
    % on top even when the figure is set as invisible (e.g., inline backend)
    global Gc8i96uVM
    if Gc8i96uVM.builtin
        f=builtin('figure',varargin{:});
        if nargout
            ret = f;
        end
    else
        if nargin > 0
            if isgraphics(varargin{1})
                f=varargin{1};
                % Trick to avoid that figure(f) makes the figure specified by f
                % the current figure and displays it on top of all other figures
                set(groot,'CurrentFigure',f);
                f=get(groot,'CurrentFigure');
                if length(varargin) > 1
                    set(f,varargin{2:end});
                end
            elseif isnumeric(varargin{1})
                n=varargin{1};
                f=builtin('figure',n);
                if length(varargin) > 1
                    set(f,varargin{2:end});
                end
            else
                f=builtin('figure',(varargin{1:end}));
            end
        else
            f=builtin('figure');
        end
        if nargout
            ret = f;
        end
    end
end