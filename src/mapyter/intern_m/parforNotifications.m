% Copyright (c) 2019 Andrea Alberti
%
% All rights reserved.

classdef parforNotifications < handle
    
    properties
        width = 50;
        showWarning = true;
    end
    
    properties (GetAccess = public, SetAccess = private)
        n;
        N;   % number of iterations
    end

    properties (GetAccess = public, SetAccess = public)
    	text = 'Please wait ...';   % text to show
    end
    
    properties (Access = private)
        inProgress = false;
        percent;
        DataQueue;
        usePercent;
        Nstr;
        NstrL;
        lastComment;
        showETA;
        times;
        numWorkers;
        oldSlope;
        isOnWorker_;
        id;
        cleanAfter;  % only when in jupyter
        inJupyter;
    end
    
    methods
        function this = parforNotifications(varargin)
            
            this.setUniqueIdentifier(4);
            this.percent = 0;
            this.lastComment = '';
            
            this.DataQueue = parallel.pool.DataQueue;
            afterEach(this.DataQueue, @this.updateStatus);

            p = inputParser;
            addParameter(p,'message','Please wait: ');
            addParameter(p,'usePercentage',true);
            addParameter(p,'showETA',false);
            addParameter(p,'initialStep',1);
            addParameter(p,'numberSteps',100);
            addParameter(p,'cleanAfter',false);  % option only for Jupyter -- remove the the progress bar after completion
            
            parse(p,varargin{:});
            
            this.N = p.Results.numberSteps;
            assert(isscalar(this.N) && isnumeric(this.N) && this.N == floor(this.N) && this.N>0, 'Error: ''numberSteps'' must be a scalar positive integer.');
            
            this.n = p.Results.initialStep;
            assert(isscalar(this.n) && isnumeric(this.n) && this.n == floor(this.n) && this.n>0, 'Error: ''initialStep'' must be a scalar positive integer.');
            this.n = this.n - 1;
            
            this.times = repmat(datetime(0,1,1),1,this.N+1);
            
            this.text = p.Results.message;
            assert(ischar(this.text), 'Error: ''Message'' must be a string.');
            
            this.usePercent = p.Results.usePercentage;
            assert(isscalar(this.usePercent) && islogical(this.usePercent), 'Error: ''usePercentage'' must be a logical scalar.');
            
            this.showETA = p.Results.showETA;
            assert(isscalar(this.showETA) && islogical(this.showETA), 'Error: ''showETA'' must be a logical scalar.');
            
            this.cleanAfter = p.Results.cleanAfter;
            assert(isscalar(this.cleanAfter) && islogical(this.cleanAfter), 'Error: ''cleanAfter'' must be a logical scalar.');
            
            this.inJupyter = inJupyter();
            
            this.PB_reprint();
            %{
            if this.usePercent
                fprintf('%s [%s]: %3d%%\n',this.text, char(32*ones(1,this.width)),0);
            else
                this.Nstr = sprintf('%d',this.N);
                this.NstrL = numel(this.Nstr);
                fprintf('%s [%s]: %s/%s\n',this.text, char(32*ones(1,this.width)),[char(32*ones(1,this.NstrL-1)),'0'],this.Nstr);
            end
            
            if this.n>0
                this.n = this.n-1;
                this.updateStatus('');
            end
            %}
            
            if this.showETA
                this.times(1) = datetime('now');
            end
            
            this.oldSlope = nan;
            
            %  PB_start
            gcp_h = gcp('nocreate');
            if isempty(gcp_h)
                this.numWorkers = 1;
            else
                this.numWorkers = gcp_h.NumWorkers;
            end
            this.inProgress = true;
        end
        
        % For backword compatibility
        function PB_iterate(this,varargin)
            this.PB_step(varargin{:});
        end
        
        % Iterate progress bar
        function PB_step(this,str,h_fct)
            if nargin <= 2
                h_fct = [];
                if nargin <= 1
                    str = '';
                end
            end
            
            str = struct('Action','UpdatePB','Message',str,'Function',h_fct,'inParfor',this.isOnWorker());
            
            if str.inParfor
                send(this.DataQueue,str);
            else
                this.updateStatus(str);
            end
        end
        
        function print(this,msg)
            data = struct('Action','Print','Message',msg);
            send(this.DataQueue,data);
        end
        
        function warning(this,warn_id,msg)
            if this.showWarning
                data = struct('Action','Warning','Id',warn_id,'Message',msg);
                send(this.DataQueue,data);
            end
        end
        
        function PB_reprint(this)
            p = round(100*this.n/this.N);
            
            this.percent = p;
            
            cursor_pos=1+round((this.width-1)*p/100);
            
            if p < 100
                sep_char = '|';
            else
                sep_char = '.';
            end
            
            if this.inJupyter
                global Gc8i96uVM;
                fid=fopen(Gc8i96uVM.pipe,'wb');
                fwrite(fid,[uint8(jsonencode(struct('cmd','tqdm','id',this.id,'value',this.n,'total',this.N,'msg',this.text,'clean',this.cleanAfter))),0]);
                fclose(fid);
            else
                if this.usePercent
                    fprintf('%s [%s%s%s]: %3d%%\n', this.text, char(46*ones(1,cursor_pos-1)), sep_char, char(32*ones(1,this.width-cursor_pos)),p);
                else
                    nstr=sprintf('%d',this.n);
                    fprintf('%s [%s%s%s]: %s/%s\n', this.text, char(46*ones(1,cursor_pos-1)), sep_char, char(32*ones(1,this.width-cursor_pos)),[char(32*ones(1,this.NstrL-numel(nstr))),nstr],this.Nstr);
                end
            end
        end
        
    end
    
    methods (Access=private)
        
        function updateStatus(this,data)
            
            switch data.Action
                case 'UpdatePB'
                    
                    this.n = this.n + 1;
                    
                    if this.inJupyter
                        global Gc8i96uVM;
                        fid=fopen(Gc8i96uVM.pipe,'wb');
                        fwrite(fid,[uint8(jsonencode(struct('cmd','tqdm','id',this.id,'value',this.n,'total',this.N,'msg',this.text,'clean',this.cleanAfter))),0]);
                        fclose(fid);
                    else
                        
                        p = round(100*this.n/this.N);
                        
                        if this.showETA
                            this.times(this.n+1) = datetime('now');
                            
                            if data.inParfor
                                idxs = this.n:-this.numWorkers:1;
                            else
                                idxs = this.n:-1:1;
                            end
                            
                            if length(idxs) < 2
                                ETAstr = '';
                            else
                                elapsedTimes = milliseconds(this.times(idxs+1)-this.times(1));
                                
                                slope = (elapsedTimes(1)-elapsedTimes(end))/(idxs(1)-idxs(end));
                                
                                s = 0.6;
                                if isnan(this.oldSlope)
                                    this.oldSlope = slope;
                                else
                                    this.oldSlope = (s*this.oldSlope + slope)/(1+s);
                                end
                                
                                ETA = this.times(this.n+1)+milliseconds(this.oldSlope*(this.N-this.n));
                                ETAstr = char(ETA);
                            end
                        else
                            ETAstr = '';
                        end
                        
                        if ~isempty(data.Function)
                            data.Function();
                        end
                        
                        if p >= this.percent+1 || this.n == this.N
                            this.percent = p;
                            
                            cursor_pos=1+round((this.width-1)*p/100);
                            
                            if p < 100
                                sep_char = '|';
                            else
                                sep_char = '.';
                            end
                            
                            if ~isempty(data.Message)
                                if ~isempty(ETAstr)
                                    comment = [' (ETA: ',ETAstr,'; ',data,')'];
                                else
                                    comment = [' (',data.Message,')'];
                                end
                            else
                                if ~isempty(ETAstr)
                                    comment = [' (ETA: ',ETAstr,')'];
                                else
                                    comment = '';
                                end
                            end
                            
                            if this.usePercent
                                fprintf('%s%s%s%s]: %3d%%%s\n',char(8*ones(1,58+numel(this.lastComment))), char(46*ones(1,cursor_pos-1)), sep_char, char(32*ones(1,this.width-cursor_pos)),p,comment);
                            else
                                nstr=sprintf('%d',this.n);
                                fprintf('%s%s%s%s]: %s/%s%s\n',char(8*ones(1,55+2*numel(this.Nstr)+numel(this.lastComment))), char(46*ones(1,cursor_pos-1)), sep_char, char(32*ones(1,this.width-cursor_pos)),[char(32*ones(1,this.NstrL-numel(nstr))),nstr],this.Nstr,comment)
                            end
                            
                            this.lastComment = comment;
                            
                            if p == 100
                                this.inProgress = false;
                            end
                        end
                    end
                case 'Warning'
                    warning(data.Id,[data.Message,newline]);
                    if this.inProgress
                        this.PB_reprint();
                    end
                    
                case 'Print'
                    disp(data.Message);
                    if this.inProgress
                        this.PB_reprint();
                    end
            end
        end
        
        function retval = isOnWorker(this)
            if isempty(this.isOnWorker_)
                this.isOnWorker_ = ~isempty(getCurrentTask());
            end
            retval = this.isOnWorker_;
        end
        
        function setUniqueIdentifier(this,len)
            %  chars = setdiff('!':'~','"\`');
            chars = '!#$&''()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}~';
            this.id = chars(randi([1,90],1,len));
        end
        
    end
    
end