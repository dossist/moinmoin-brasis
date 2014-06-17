"""
    brasis.py - Line break preservation

    Default wiki parser with preserved line breaks.

    Restriction:
        Line break preservation in tables are not supported.
        You can still use <<BR>> in tables.

    Tested with:
        MoinMoin 1.9.7

    Thanks to:
        DavidMontgomery for nice tweaks, this plugin is based on his idea.
        MoinMoin developpers and contributors.

    @copyright: 2014 dossist.
    @license: GNU GPL, see http://www.gnu.org/licenses/gpl for details.
"""

import re
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser

Dependencies = ['user']

def list_in_groupdict(keylist, groupdict):
    """
    checks if dictionary 'groupdict' has at least one key in list 'keylist'
    """
    for key in keylist:
        if key in groupdict and groupdict[key] is not None:
            return True
    return False

class Parser(WikiParser):
    # No line-break elements
    #   List of group labels defined in WikiParser.scan_rules (see original parser).
    #   Suppress <br> insertion to current line (nobreak_now) and to the next line (nobreak_next)
    #   when we find those elements in current line.
    nobreak_now  = ['li', 'li_none', 'ol', 'dl', 'table']
    nobreak_next = ['heading', 'table']

    def __init__(self, raw, request, **kw):
        WikiParser.__init__(self, raw, request, **kw)
        # state holders carried over lines
        self.break_next = False # can <br> be inserted in the next line?
        self.prev_list = False # were we in a list in the previous line?

    def format(self, formatter):
        """
        same as original but resetting state holders at the end
        """
        WikiParser.format(self, formatter)
        # reset those states every time format is done
        self.break_next = False
        self.prev_list = False

    def scan(self, line, inhibit_p=False):
        """
        pass line to the original method, then modify the result.

        * if we need <br> for the current line, we just indicate that the next line should begin with <br>,
          and move on to the next line doing nothing to the current line.
        * if the previous line needed <br>, we check whether current line is 'breakable',
          and finally add <br> at the beginning of the output from original scan() method if conditions are met.
        """
        formatted_line = WikiParser.scan(self, line, inhibit_p=inhibit_p)

        # match wiki patterns again to know what context we are in
        match = self.scan_re.search(line)
        if match:
            match_dict = match.groupdict()
        else:
            match_dict = {}

        # check if current line can be line-broken
        break_now = not (list_in_groupdict(self.nobreak_now, match_dict) or # current line
                        self.in_table or self.in_pre or # no-linebreak states carried over lines
                        (self.prev_list is not self.in_list) or # need this when quitting from lists
                        self.line_was_empty) # finally we don't need line breaks for paragraph ends
        # if conditions are met, append a br tag
        if break_now and self.break_next:
            formatted_line = self.formatter.linebreak(preformatted=0) + formatted_line
        # in certain structures, we don't want line breaks in the next line
        self.break_next = not (list_in_groupdict(self.nobreak_next, match_dict) or
                               self.in_table or self.in_pre)
        # save current in_list status
        self.prev_list = self.in_list

        return formatted_line