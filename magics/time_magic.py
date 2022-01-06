# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from mapyter._MagicPosix import MagicPosix
import time


class TimeMagic(MagicPosix):

    def cell_time(self, line, code, **kwargs):
        """
Show execution time for the cell.

Example:

%%time

disp('This is Matlab code taking long time');

pause(1);

disp('And now it is finished.');
"""
        self.start = time.time()

    def post_process(self, retval):
        if self.evaluate:
            result = "Time: %s seconds.\n" % (time.time() - self.start)
            self.kernel.Print(result)
            return retval

def register_magics(kernel):
    kernel.register_magics(TimeMagic)