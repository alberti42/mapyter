function shareWithJupyter()
    
    actualEngineName = matlab.engine.engineName;
    username = char(java.lang.System.getProperty('user.name'));
    engineName = ['jupyter_',username];
    
    if isempty(actualEngineName)
        matlab.engine.shareEngine(engineName);
    else
        if ~strcmp(actualEngineName,engineName)
            error('Error. MATLAB session is already shared as "%s" instead of "%s"',actualEngineName,engineName);
        end
    end
    
end