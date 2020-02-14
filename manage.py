#!/usr/bin/env python
import os
import sys
import websocket_server


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings")

    from django.core.management import execute_from_command_line

    if(sys.argv[1] == "runserver"): 
        websocket_server.launch_server() # spawns async server thread

    execute_from_command_line(sys.argv) # launch django as normal
    