from celery import Celery
import os

celery = Celery("nexus-celery",
                broker="redis://localhost",
                backend = "redis://localhost"
                )

#gather tasks
dir = os.path.join(os.path.dirname(__file__), "tasks")
tasks_dirs = ["taskmanager.tasks." + name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
tasks_dirs.remove("taskmanager.tasks.__pycache__")

celery.autodiscover_tasks(tasks_dirs)