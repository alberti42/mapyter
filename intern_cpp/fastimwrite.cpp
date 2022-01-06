#include <fstream>
#include <cstring>
// #include <iostream>
// #include <iomanip>
// #include <string>

#include "matrix.h"
#include "mex.h"

using namespace std;

void mexFunction(int nlhs, mxArray *plhs[],int nrhs, const mxArray *prhs[])
{
	const char* path = reinterpret_cast<const char *>(mxArrayToString(prhs[0]));
	const char* hash = reinterpret_cast<const char *>(mxArrayToString(prhs[1]));
	const char* img = reinterpret_cast<const char*>(mxGetPr(prhs[2]));

	mwSize numDims = mxGetNumberOfDimensions(prhs[2]);
	
	if(numDims==3)
	{
		const mwSize *dims = mxGetDimensions(prhs[2]);
		const mwSize& w = dims[1];
		const mwSize& h = dims[2];
		
		ofstream fifo;
		fifo.open(path, ofstream::out|ofstream::binary);
		fifo << "{\"cmd\":\"import\",\"type\":\"image\",\"format\":\"RGB\",\"width\":"<< \
			w << ",\"height\":" << h << ",\"hash\":\"" << hash << "\"}" << '\0';
		fifo.write(img,h*w*3);
		fifo.close();
	}
}