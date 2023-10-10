from celery import Celery
import os

celery = Celery("nexus-celery",
                broker="redis://localhost:6379/0",
                backend = "redis://localhost:6379/1"
                )

#gather tasks
dir = os.path.join(os.path.dirname(__file__), "tasks")
tasks_dirs = ["taskmanager.tasks." + name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
if "taskmanager.tasks.__pycache__" in tasks_dirs:   
    tasks_dirs.remove("taskmanager.tasks.__pycache__")

celery.set_default()
celery.autodiscover_tasks(tasks_dirs)
