function clc()
    % Overwrite the built-in clc function to clear the output in jupyter
    global Gc8i96uVM
    if Gc8i96uVM.builtin
    	builtin('clc');
    else
    	fprintf('[Gc8i96uVM, clc]\n');
    end
end