import os
import libtmux

server = libtmux.Server()

#set session name
session = server.new_session(session_name= "Nexus")
#create windows
core = session.attached_window.rename_window("Core")
comms = session.new_window(window_name= "Comms")
taskmng = session.new_window(window_name= "taskmng")
database = session.new_window(window_name= "Database")

#startup nexus services
database.attached_pane.send_keys("python3 database/__main__.py")
comms.attached_pane.send_keys("python3 communications/__main__.py")
taskmng.attached_pane.send_keys("python3 taskmanager/__main__.py")
core.attached_pane.send_keys("python3 core/__main__.py")
