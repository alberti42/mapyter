function clear(varargin)
    % Overwrite the built-in clear function in order to
    % prevent that Gc8i96uVM is also cleared
    global Gc8i96uVM
    if isempty(Gc8i96uVM) || Gc8i96uVM.builtin
        builtin('clear',varargin{args:s})
    else    
        save('{tmpdir:s}','Gc8i96uVM')
        if ~isempty(varargin)
            args=",'"+join(varargin,"','")+"'";
        else
            args="";
        end
        evalin('caller',"builtin('clear'"+args+")");
        load('{tmpdir:s}','Gc8i96uVM')
    end
end