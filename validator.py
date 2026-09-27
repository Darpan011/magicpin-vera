import re


class MessageValidator:

    MAX_LENGTH = 500

    def validate(
        self,
        message,
        context,
        strategy
    ):

        # =====================================================
        # BASIC VALIDATION
        # =====================================================

        if not message:
            return False, "empty_message"

        body = message.get(
            "body",
            ""
        ).strip()

        if not body:
            return False, "empty_body"

        if len(body) > self.MAX_LENGTH:
            return False, "message_too_long"


        # =====================================================
        # CTA VALIDATION
        # =====================================================

        cta = message.get(
            "cta"
        )

        if cta not in [
            "YES",
            "STOP",
            None
        ]:
            return False, "invalid_cta"


        # =====================================================
        # SEND_AS VALIDATION
        # =====================================================

        send_as = message.get(
            "send_as"
        )

        if send_as not in [
            "template",
            "freeform"
        ]:
            return False, "invalid_send_as"


        # =====================================================
        # PLACEHOLDER DETECTION
        # =====================================================

        forbidden_placeholders = [
            "TBD",
            "YOUR_NAME",
            "YOUR_EMAIL",
            "[insert",
            "[price",
            "[date",
            "<price>",
            "<date>"
        ]

        body_lower = body.lower()

        for item in forbidden_placeholders:

            if item.lower() in body_lower:
                return False, "placeholder_detected"


        # =====================================================
        # URL VALIDATION
        # =====================================================

        urls = re.findall(
            r"https?://\S+",
            body
        )

        if len(urls) > 1:
            return False, "too_many_urls"


        # =====================================================
        # UNSUPPORTED ACTION CLAIMS
        # =====================================================

        unsupported_action_patterns = [

            r"\bi('?ve| have) started\b",

            r"\bstarted the process\b",

            r"\bi('?ve| have) submitted\b",

            r"\bsubmitted (it|this|the)\b",

            r"\bi('?ve| have) verified\b",

            r"\bverified (your|the) profile\b",

            r"\bi('?ve| have) updated\b",

            r"\bupdated (your|the) profile\b",

            r"\bi('?ve| have) changed\b",

            r"\bbooked (your|the) appointment\b",

            r"\bi('?ve| have) booked\b",

            r"\bappointment is booked\b",

            r"\bi('?ve| have) contacted\b",

            r"\bcontacted google\b",

            r"\bcontacted magicpin\b",

            r"\bi('?ll| will) update you\b",

            r"\bi('?ll| will) get back to you\b",

            r"\bi('?ll| will) send you an update\b",

            r"\bi('?ll| will) notify you\b",

            r"\bi('?ll| will) monitor\b",

            r"\bi('?ll| will) take care of it\b"
        ]

        for pattern in unsupported_action_patterns:

            if re.search(
                pattern,
                body_lower
            ):

                return False, (
                    "unsupported_action_claim"
                )


        # =====================================================
        # UNSUPPORTED CAUSAL CLAIMS
        # =====================================================

        causal_patterns = [

            r"\bwill increase\b",

            r"\bwill improve\b",

            r"\bwill boost\b",

            r"\bwill bring more\b",

            r"\bwill get you more\b",

            r"\bwill attract more\b",

            r"\bhelps? (you )?get more\b",

            r"\bhelps? (you )?bring more\b",

            r"\bcaused by\b",

            r"\bthe reason .* is\b",

            r"\bresults in\b",

            r"\bleads to\b"
        ]

        for pattern in causal_patterns:

            if re.search(
                pattern,
                body_lower
            ):

                return False, (
                    "unsupported_causal_claim"
                )


        # =====================================================
        # UNSUPPORTED SPECIFIC DETAILS
        # =====================================================

        # These are common details Gemini may invent when
        # they are not present in the supplied context.

        unsupported_details = [

            "verification postcard",

            "postcard verification",

            "verification code",

            "otp",

            "discount code",

            "coupon code",

            "booking confirmation",

            "payment confirmation"
        ]

        for detail in unsupported_details:

            if detail in body_lower:

                # Only reject if the detail isn't actually
                # present in the supplied context.
                context_text = str(
                    context
                ).lower()

                if detail not in context_text:

                    return False, (
                        "unsupported_specific_detail"
                    )


        # =====================================================
        # MEDICAL / CLINICAL SAFETY
        # =====================================================

        category = (
            context.get("category")
            or {}
        )

        category_text = str(
            category
        ).lower()

        medical_categories = [
            "dentist",
            "dental",
            "pharmacy",
            "medical",
            "clinic"
        ]

        is_medical = any(
            x in category_text
            for x in medical_categories
        )

        if is_medical:

            dangerous_claims = [

                "100% safe",

                "guaranteed cure",

                "guaranteed",

                "completely cures",

                "miracle",

                "best in city",

                "best in the city",

                "zero risk",

                "no side effects",

                "permanent cure"
            ]

            for claim in dangerous_claims:

                if claim in body_lower:

                    return False, (
                        "unsafe_medical_claim"
                    )


        # =====================================================
        # WORD-FORMATTING CHECK
        # =====================================================

        formatting_patterns = [

            r"\d+[a-zA-Z]+",

            r"[a-zA-Z]+verification",

            r"[a-zA-Z]+profile",

            r"[a-zA-Z]+listing"
        ]

        for pattern in formatting_patterns:

            if re.search(
                pattern,
                body
            ):

                # Ignore normal URLs because those are
                # handled separately.
                if "http://" not in body_lower and \
                   "https://" not in body_lower:

                    return False, (
                        "possible_word_concatenation"
                    )


        # =====================================================
        # FINAL VALID
        # =====================================================

        return True, "valid"