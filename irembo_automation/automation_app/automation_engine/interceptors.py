# automation_app/automation_engine/interceptors.py
class InterceptorMixin:
    def _intercept_resources(self, route):
        ignored_types = ["image", "font", "stylesheet", "media"]
        if route.request.resource_type in ignored_types or "analytics" in route.request.url.lower():
            route.abort()
        else:
            route.continue_()