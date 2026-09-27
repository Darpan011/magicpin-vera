class ContextStore:
    def __init__(self):
        self.data = {
            "category": {},
            "merchant": {},
            "customer": {},
            "trigger": {}
        }

        self.versions = {
            "category": {},
            "merchant": {},
            "customer": {},
            "trigger": {}
        }

    def store(self, scope, context_id, version, payload):
        if scope not in self.data:
            return False, "invalid_scope"

        current_version = self.versions[scope].get(context_id, -1)

        # Ignore stale or duplicate versions
        if version <= current_version:
            return False, "stale_version"

        # Store the latest version
        self.data[scope][context_id] = payload
        self.versions[scope][context_id] = version

        return True, None

    def get(self, scope, context_id):
        return self.data.get(scope, {}).get(context_id)

    def count(self, scope):
        return len(self.data.get(scope, {}))

    def counts(self):
        return {
            "category": self.count("category"),
            "merchant": self.count("merchant"),
            "customer": self.count("customer"),
            "trigger": self.count("trigger")
        }