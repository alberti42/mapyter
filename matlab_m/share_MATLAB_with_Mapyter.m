function shareWithJupyter(name)
    
    actualEngineName = matlab.engine.engineName;
    if nargin == 1
        engineName = name;
    else
        engineName = 'mapyter';
    end
    
    if isempty(actualEngineName)
        matlab.engine.shareEngine(engineName);
    else
        if ~strcmp(actualEngineName,engineName)
            error('Error. MATLAB session is already shared as "%s" instead of "%s"',actualEngineName,engineName);
        end
    end
    
end