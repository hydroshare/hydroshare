from health_check.backends import BaseHealthCheckBackend
from datetime import datetime, timedelta


class PeriodicTasksHealthCheck(BaseHealthCheckBackend):
    critical_service = True

    def check_status(self):
        try:
            with open("celery/periodic_tasks_last_executed.txt", mode='r') as file:
                datetime_string = file.read().rstrip()
            dt = datetime.strptime(datetime_string, '%m/%d/%y %H:%M:%S')
            cutoff_date = datetime.now() - timedelta(days=1)
            if dt < cutoff_date:
                self.add_error(f"Celery job last run {dt.strftime('%m/%d/%Y')}")
        except FileNotFoundError:
            self.add_error("periodic_tasks_last_executed.txt file not found")

    def identifier(self):
        return self.__class__.__name__  # Display name on the endpoint.
