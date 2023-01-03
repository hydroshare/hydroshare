from health_check.backends import BaseHealthCheckBackend


class HsHealthCheckBackend(BaseHealthCheckBackend):
    critical_service = True

    def check_status(self):
        # TODO #4888
        # The test code goes here.
        # You can use `self.add_error` or
        # raise a `HealthCheckException`,
        # similar to Django's form validation.
        pass

    def identifier(self):
        return self.__class__.__name__  # Display name on the endpoint.
