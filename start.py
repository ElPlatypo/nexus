import os
import libtmux

server = libtmux.Server()

os.system("sudo service postgresql start")

#set session name
session = server.new_session(session_name= "Nexus")
#create windows
core = session.attached_window.rename_window("Core")
comms = session.new_window(window_name= "Comms")
celery = session.new_window(window_name= "Celery")
taskmng = session.new_window(window_name= "Taskmng")
database = session.new_window(window_name= "Database")
inference = session.new_window(window_name= "Inference")

#startup nexus services
database.attached_pane.send_keys("pgadmin4")
comms.attached_pane.send_keys("python3 communications/__main__.py")
taskmng.attached_pane.send_keys("python3 taskmanager/__main__.py")
core.attached_pane.send_keys("python3 core/__main__.py")
inference.attached_pane.send_keys("python3 inference/__main__.py")
celery.attached_pane.send_keys("celery -A taskmanager.celery.celery worker -l INFO")
