"""Perform DOI activation task."""


class HSTaskRouter(object):
    """Perform DOI activation task."""

    def route_for_task(self, task, args=None, kwargs=None):
        """Return exchange, exchange_type, and routing_key."""
        if task == 'hs_core.tasks.manage_task_hourly':
            return {
                'exchange': 'default',
                'exchange_type': 'topic',
                'routing_key': 'task.default',
            }

        return None
