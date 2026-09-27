import re


class ConversationHandler:

    STOP_WORDS = {
        "stop",
        "unsubscribe",
        "don't message",
        "dont message",
        "do not message",
        "no thanks",
        "not interested",
        "not interested now",
        "leave me alone",
        "no need"
    }

    POSITIVE_WORDS = {
        "yes",
        "yeah",
        "yep",
        "sure",
        "okay",
        "ok",
        "do it",
        "go ahead",
        "please do",
        "sounds good",
        "interested"
    }

    def classify(
        self,
        message,
        conversation
    ):

        text = message.strip().lower()

        # ---------------------------------------------
        # 1. EXPLICIT OPT-OUT
        # ---------------------------------------------

        if self.is_stop(text):
            return "stop"


        # ---------------------------------------------
        # 2. AUTO-REPLY DETECTION
        # ---------------------------------------------

        if (
            conversation.get(
                "repeated_count",
                0
            ) >= 3
        ):
            return "auto_reply"


        # ---------------------------------------------
        # 3. INTENT TRANSITIONS
        # ---------------------------------------------

        if self.is_offer_request(text):
            return "offer_drafting"

        if self.is_gst_request(text):
            return "off_topic_gst"

        if self.is_profile_request(text):
            return "profile_help"


        # ---------------------------------------------
        # 4. POSITIVE CONTINUATION
        # ---------------------------------------------

        if self.is_positive(text):
            return "continue"


        # ---------------------------------------------
        # 5. NORMAL MESSAGE
        # ---------------------------------------------

        return "normal"


    # =================================================
    # STOP DETECTION
    # =================================================

    def is_stop(self, text):

        text = self.normalize(text)

        for phrase in self.STOP_WORDS:

            if self.contains_phrase(
                text,
                phrase
            ):
                return True

        return False


    # =================================================
    # POSITIVE RESPONSE DETECTION
    # =================================================

    def is_positive(self, text):

        text = self.normalize(text)

        # Exact match first
        if text in self.POSITIVE_WORDS:
            return True

        # Phrase matching
        for phrase in self.POSITIVE_WORDS:

            if len(phrase) <= 3:
                continue

            if self.contains_phrase(
                text,
                phrase
            ):
                return True

        return False


    # =================================================
    # OFFER REQUEST
    # =================================================

    def is_offer_request(self, text):

        keywords = [
            "offer",
            "discount",
            "promotion",
            "promo",
            "deal",
            "draft"
        ]

        return self.contains_keyword(
            text,
            keywords
        )


    # =================================================
    # GST / TAX REQUEST
    # =================================================

    def is_gst_request(self, text):

        return (
            self.contains_phrase(
                text,
                "gst"
            )
            or self.contains_phrase(
                text,
                "tax filing"
            )
            or self.contains_phrase(
                text,
                "file my tax"
            )
        )


    # =================================================
    # PROFILE REQUEST
    # =================================================

    def is_profile_request(self, text):

        keywords = [
            "profile",
            "listing",
            "visibility",
            "gbp",
            "google profile"
        ]

        return self.contains_keyword(
            text,
            keywords
        )


    # =================================================
    # HELPERS
    # =================================================

    @staticmethod
    def normalize(text):

        text = text.lower().strip()

        # Convert punctuation to spaces
        text = re.sub(
            r"[^\w\s]",
            " ",
            text
        )

        # Remove repeated whitespace
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    @staticmethod
    def contains_phrase(
        text,
        phrase
    ):

        phrase = phrase.lower().strip()

        # Word-boundary matching prevents
        # accidental substring matches.
        pattern = (
            r"\b"
            + re.escape(phrase)
            + r"\b"
        )

        return re.search(
            pattern,
            text
        ) is not None


    @staticmethod
    def contains_keyword(
        text,
        keywords
    ):

        for keyword in keywords:

            if ConversationHandler.contains_phrase(
                text,
                keyword
            ):
                return True

        return False