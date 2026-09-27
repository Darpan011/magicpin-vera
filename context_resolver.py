class ContextResolver:

    def __init__(self, store):
        self.store = store

    def resolve(self, trigger):

        merchant_id = trigger.get("merchant_id")
        customer_id = trigger.get("customer_id")

        merchant = self.store.get(
            "merchant",
            merchant_id
        )

        customer = None

        if customer_id:
            customer = self.store.get(
                "customer",
                customer_id
            )

        category = None

        if merchant:

            # First try explicit category_id
            category_id = merchant.get("category_id")

            if category_id:
                category = self.store.get(
                    "category",
                    category_id
                )

            # Dataset uses category_slug
            if category is None:

                category_slug = merchant.get(
                    "category_slug"
                )

                if category_slug:

                    # Try direct lookup first
                    category = self.store.get(
                        "category",
                        category_slug
                    )

                    # If the category store uses a different ID,
                    # search loaded category payloads by slug.
                    if category is None:

                        for category_data in self.store.data.get(
                            "category",
                            {}
                        ).values():

                            if not isinstance(
                                category_data,
                                dict
                            ):
                                continue

                            if (
                                category_data.get("slug")
                                == category_slug
                                or
                                category_data.get("category_slug")
                                == category_slug
                            ):
                                category = category_data
                                break

        return {
            "trigger": trigger,
            "merchant": merchant,
            "customer": customer,
            "category": category,
        }