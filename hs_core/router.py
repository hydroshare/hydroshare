class HSTaskRouter(object):

    def route_for_task(self, task, args=None, kwargs=None):

        if task == 'hs_core.tasks.check_doi_activation':
            return {
                'exchange': 'default',
                'exchange_type': 'topic',
                'routing_key': 'task.default',
            }

        return None
