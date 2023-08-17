from mapyter._MagicPosix import MagicPosix, option, ArgumentError

from mapyter.helper_fcnts import validatestring, InvalidStringError

max_num_arg = ('-n', '--max-num')
summary_arg = ('-s', '--show-summary')
group_arg = ('-g', '--group-similar')
log_arg = ('-l', '--log')

ORANGE = '\x1b[38;2;255;100;0m'
NORMAL = '\x1b[0m'

class MuteMatlabWarningsMagic(MagicPosix):

    @option(*max_num_arg, action='store', metavar='NUM', default=1, type=int, help='Maximum number of warnings displayed per each kind before silencing them (default: %(default)s)')
    @option(*summary_arg, action='store', metavar='{yes,no}', type=str, default='yes', help='Show after completion a summary of warnings that were silenced during execution (default: %(default)s)')
    @option(*log_arg, action='store', metavar='{yes,no}', type=str, default='yes', help='Show silenced warnings in the log panel (default: %(default)s)')
    @option(*group_arg, action='store', metavar='{yes,no}', type=str, default='no', help='Group warnings from the same code line as the same warning, regardless of their possibly different message (default: %(default)s)')
    def line_mute_matlab_warnings(self,line,code,**kwargs):
        """
Mute repeated MATLAB warnings if their number exceeds NUM. With --show-summary, a summary of warnings is displayed after code execution.
Note that if warnings emitted from the same code line are groupped together with --group-similar, only the message of the warning emitted first will be displayed in the summary, when --show-summary is selected. 
"""

        summary = kwargs['show_summary']
        try:
            summary = True if validatestring(summary,('yes','no')) == "yes" else False
        except InvalidStringError as e:
            raise ArgumentError(summary_arg,msg=str(e).lower(),magic='mute_matlab_warnings')

        group = kwargs['group_similar']
        try:
            group = True if validatestring(group,('yes','no')) == "yes" else False
        except InvalidStringError as e:
            raise ArgumentError(group_arg,msg=str(e).lower(),magic='mute_matlab_warnings')

        log = kwargs['log']
        try:
            log = True if validatestring(log,('yes','no')) == "yes" else False
        except InvalidStringError as e:
            raise ArgumentError(log_arg,msg=str(e).lower(),magic='mute_matlab_warnings')
        
        max_num = kwargs['max_num']
        if max_num<0:
            raise ArgumentError(max_num_arg,msg='only positive integers are permitted',magic='mute_matlab_warnings')
        
        self.kernel._warnings = {'max_num':max_num,'summary':summary,'group':group,'log':log}

        self.evaluate = True

    def post_process(self, retval):
        if self.evaluate:
            if self.kernel._warnings['summary']:
                max_num = self.kernel._warnings['max_num']
                msgs = []
                for warning in self.kernel._warnings_log.values():
                    if warning['count'] > max_num:
                        msg = warning['msg']
                        msgs.append(msg[0] + ' (total number: {:d})'.format(warning['count']) + msg[1])
                if msgs:
                    self.kernel.Write(ORANGE + "Summary of silenced warnings:\n-----------------------------\n" + "".join(msgs) + NORMAL)

def register_magics(kernel):
    kernel.register_magics(MuteMatlabWarningsMagic)
