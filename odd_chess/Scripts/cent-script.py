#!c:\users\ayliu\my_things\college_work\ic60\odd_chess\odd_chess\scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'cent==2.1.0','console_scripts','cent'
__requires__ = 'cent==2.1.0'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('cent==2.1.0', 'console_scripts', 'cent')()
    )
