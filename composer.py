class VeraComposer:

    def compose(self, context, strategy):
        trigger = context.get("trigger", {})
        merchant = context.get("merchant") or {}
        customer = context.get("customer")
        category = context.get("category") or {}

        kind = trigger.get("kind", "")

        if kind == "perf_dip":
            return self.performance_dip(merchant, trigger)

        if kind == "perf_spike":
            return self.performance_spike(merchant, trigger)

        if kind == "recall_due":
            return self.recall_due(merchant, customer, trigger)

        if kind in ["customer_lapsed_soft", "winback"]:
            return self.winback(merchant, customer, trigger)

        if kind in ["chronic_refill", "chronic_refill_due"]:
            return self.chronic_refill(merchant, customer, trigger)

        if kind == "research_digest":
            return self.research_digest(
                merchant,
                category,
                trigger
            )

        if kind == "competitor_opened":
            return self.competitor_response(
                merchant,
                trigger
            )

        if kind == "festival":
            return self.festival_opportunity(
                merchant,
                category,
                trigger
            )

        if kind == "milestone_reached":
            return self.milestone_reached(
                merchant,
                trigger
            )

        if kind == "dormant_with_vera":
            return self.dormant_merchant(
                merchant,
                trigger
            )

        if kind == "unverified_gbp":
            return self.profile_improvement(
                merchant,
                trigger
            )

        if kind == "curious_ask":
            return self.curious_merchant(
                merchant,
                trigger
            )

        if kind == "appointment_tomorrow":
            return self.appointment_followup(
                merchant,
                customer,
                trigger
            )

        if kind == "compliance":
            return self.compliance_guidance(
                merchant,
                trigger
            )

        return self.fallback(
            merchant,
            trigger
        )


    # ---------------------------------------------------------
    # PERFORMANCE
    # ---------------------------------------------------------

    def performance_dip(self, merchant, trigger):

        performance = merchant.get("performance", {})

        calls = performance.get("calls")
        baseline = performance.get("baseline_calls")

        if calls is not None and baseline is not None:
            body = (
                f"Quick flag — your recent calls are at {calls}, "
                f"vs a baseline of around {baseline}. "
                f"Want me to suggest a specific action to improve this?"
            )

        elif calls is not None:
            body = (
                f"Quick flag — your recent calls are down to {calls}. "
                f"Want me to suggest a specific action to improve this?"
            )

        else:
            body = (
                "Quick flag — your recent performance has dipped. "
                "Want me to suggest a specific action to improve this?"
            )

        return {
            "body": body,
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "perf_dip",
                trigger
            ),
            "rationale": (
                "Performance dip detected; prompt merchant "
                "toward a concrete recovery action."
            )
        }


    def performance_spike(self, merchant, trigger):

        performance = merchant.get("performance", {})
        calls = performance.get("calls")
        views = performance.get("views")

        if calls is not None:
            body = (
                f"Nice momentum — your recent calls reached {calls}. "
                "Want me to suggest how to build on it?"
            )

        elif views is not None:
            body = (
                f"Nice momentum — your recent views reached {views}. "
                "Want me to suggest how to build on it?"
            )

        else:
            body = (
                "Nice momentum on your recent performance. "
                "Want me to suggest how to build on it?"
            )

        return {
            "body": body,
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "perf_spike",
                trigger
            ),
            "rationale": "Positive performance signal detected."
        }


    # ---------------------------------------------------------
    # CUSTOMER
    # ---------------------------------------------------------

    def recall_due(self, merchant, customer, trigger):

        customer_name = (
            customer.get("name")
            if customer
            else "there"
        )

        service_due = trigger.get("service_due")
        due_date = trigger.get("due_date")
        slots = trigger.get("slots")

        body = f"Hi {customer_name}, "

        if service_due:
            body += f"your {service_due.replace('_', ' ')} is coming up"
        else:
            body += "your next visit is coming up"

        if due_date:
            body += f" around {due_date}"

        if slots:
            body += ". I can help check the available slots"
        else:
            body += ". Want me to help check availability?"

        if slots:
            body += " — want me to share them?"

        return {
            "body": body,
            "cta": "YES",
            "send_as": "template",
            "suppression_key": trigger.get(
                "suppression_key",
                self._customer_key("recall", trigger)
            ),
            "rationale": (
                "Customer recall trigger detected; "
                "use service history and available timing."
            )
        }


    def chronic_refill(self, merchant, customer, trigger):

        customer_name = (
            customer.get("name")
            if customer
            else "there"
        )

        return {
            "body": (
                f"Hi {customer_name}, your regular refill "
                "may be due. Want me to help check availability?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._customer_key(
                "refill",
                trigger
            ),
            "rationale": (
                "Chronic refill trigger detected; "
                "prompt customer toward a practical next step."
            )
        }


    def winback(self, merchant, customer, trigger):

        customer_name = (
            customer.get("name")
            if customer
            else "there"
        )

        return {
            "body": (
                f"Hi {customer_name}, it's been a while since "
                "your last visit. Want to see what's available?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._customer_key(
                "winback",
                trigger
            ),
            "rationale": "Lapsed customer detected."
        }


    # ---------------------------------------------------------
    # CATEGORY / RESEARCH
    # ---------------------------------------------------------

    def research_digest(self, merchant, category, trigger):

        digest = category.get("digest")

        if digest:
            body = (
                "I found a relevant category update "
                "that could matter for your business. "
                "Want to see the key takeaway?"
            )
        else:
            body = (
                "I found a relevant category insight "
                "for your business. Want to see the key takeaway?"
            )

        return {
            "body": body,
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "digest",
                trigger
            ),
            "rationale": "Relevant category research available."
        }


    # ---------------------------------------------------------
    # MERCHANT EVENTS
    # ---------------------------------------------------------

    def competitor_response(self, merchant, trigger):

        return {
            "body": (
                "A nearby competitor has opened recently. "
                "Want me to suggest a specific way to strengthen "
                "your listing?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "competitor",
                trigger
            ),
            "rationale": (
                "Competitive activity detected; "
                "offer a concrete response."
            )
        }


    def festival_opportunity(self, merchant, category, trigger):

        festival = (
            trigger.get("festival")
            or trigger.get("event")
            or "the upcoming festival"
        )

        return {
            "body": (
                f"{festival} is coming up. Want me to suggest "
                "a relevant offer or promotion for your business?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "festival",
                trigger
            ),
            "rationale": "Upcoming festival opportunity detected."
        }


    def milestone_reached(self, merchant, trigger):

        milestone = trigger.get("milestone")

        if milestone:
            body = (
                f"You've reached {milestone}. "
                "Want me to suggest a way to build on the momentum?"
            )
        else:
            body = (
                "You've reached an important milestone. "
                "Want me to suggest how to build on it?"
            )

        return {
            "body": body,
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "milestone",
                trigger
            ),
            "rationale": "Merchant milestone detected."
        }


    def dormant_merchant(self, merchant, trigger):

        return {
            "body": (
                "It's been a while since we've worked on your "
                "listing together. Want me to suggest one useful "
                "update to bring it back into focus?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "dormant",
                trigger
            ),
            "rationale": "Merchant dormancy detected."
        }


    def profile_improvement(self, merchant, trigger):

        return {
            "body": (
                "Your business profile still needs verification. "
                "Want me to walk you through the next step?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "profile",
                trigger
            ),
            "rationale": "Profile verification issue detected."
        }


    def curious_merchant(self, merchant, trigger):

        return {
            "body": (
                "Sure — I can help with that. "
                "Want me to look at the relevant details for your business?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "curious",
                trigger
            ),
            "rationale": "Merchant expressed curiosity or requested information."
        }


    def appointment_followup(self, merchant, customer, trigger):

        customer_name = (
            customer.get("name")
            if customer
            else "there"
        )

        return {
            "body": (
                f"Hi {customer_name}, your appointment is tomorrow. "
                "Want me to help confirm the timing?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._customer_key(
                "appointment",
                trigger
            ),
            "rationale": "Upcoming appointment detected."
        }


    def compliance_guidance(self, merchant, trigger):

        return {
            "body": (
                "There's a compliance-related update for your business. "
                "Want me to explain the specific requirement?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                "compliance",
                trigger
            ),
            "rationale": "Compliance-related trigger detected."
        }


    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    def fallback(self, merchant, trigger):

        kind = trigger.get("kind", "update")

        return {
            "body": (
                f"I have a relevant {kind.replace('_', ' ')} "
                "update for your business. Want to see it?"
            ),
            "cta": "YES",
            "send_as": "template",
            "suppression_key": self._merchant_key(
                kind,
                trigger
            ),
            "rationale": "Fallback response for unsupported trigger."
        }


    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _merchant_key(self, prefix, trigger):

        merchant_id = trigger.get("merchant_id", "unknown")

        return f"{prefix}:{merchant_id}"


    def _customer_key(self, prefix, trigger):

        customer_id = trigger.get("customer_id", "unknown")

        merchant_id = trigger.get("merchant_id", "unknown")

        return f"{prefix}:{customer_id}:{merchant_id}"