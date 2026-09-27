class DecisionEngine:

    STRATEGIES = {
        "perf_dip": "performance_recovery",
        "seasonal_perf_dip": "seasonal_performance_recovery",
        "perf_spike": "performance_momentum",

        "recall_due": "customer_recall",
        "chronic_refill_due": "customer_reorder",
        "customer_lapsed_soft": "customer_winback",
        "customer_lapsed_hard": "customer_winback",
        "winback_eligible": "customer_winback",

        "research_digest": "category_insight",
        "competitor_opened": "competitive_response",

        "festival_upcoming": "festival_opportunity",
        "category_seasonal": "seasonal_opportunity",
        "ipl_match_today": "event_opportunity",
        "wedding_package_followup": "package_followup",

        "milestone_reached": "milestone_engagement",
        "dormant_with_vera": "reactivation",

        "gbp_unverified": "profile_improvement",

        "curious_ask_due": "merchant_question",
        "active_planning_intent": "merchant_planning",
        "trial_followup": "trial_followup",
        "renewal_due": "renewal_followup",

        "appointment_tomorrow": "appointment_followup",

        "regulation_change": "compliance_guidance",
        "supply_alert": "supply_guidance",
        "cde_opportunity": "cde_opportunity",
        "review_theme_emerged": "review_insight",
    }

    def route(self, trigger):
        """
        Convert a trigger into a high-level Vera strategy.
        """

        kind = trigger.get("kind", "").lower()

        strategy = self.STRATEGIES.get(
            kind,
            "general_merchant_assistance"
        )

        return {
            "trigger_kind": kind,
            "strategy": strategy,
            "priority": trigger.get("urgency", 1),
            "customer_required": trigger.get("customer_id") is not None,
        }