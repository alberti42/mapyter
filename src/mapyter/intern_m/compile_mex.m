if exist('fastimwrite','file')~=3
    disp('MEX file ''fastimwrite'' not found. Compiling it now ...')
    mex('-setup','C++');
    mex('-compatibleArrayDims','-O','-outdir','{matlab_m:s}',fullfile('{intern_cpp:s}','fastimwrite.cpp'))
end