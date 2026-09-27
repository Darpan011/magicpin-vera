class ConversationStore:

    def __init__(self):
        self.conversations = {}

    def create(
        self,
        conversation_id,
        merchant_id,
        customer_id=None,
        trigger_id=None,
        strategy=None
    ):
        self.conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "trigger_id": trigger_id,
            "strategy": strategy,

            "messages": [],

            "turn_number": 0,

            "status": "active",

            "intent": strategy,

            # Track merchant messages separately
            "last_merchant_message": None,

            # Number of consecutive identical merchant messages
            "repeated_count": 0,

            # Number of merchant turns without a meaningful
            # intent transition
            "merchant_turns": 0
        }

        return self.conversations[conversation_id]

    def get(self, conversation_id):
        return self.conversations.get(
            conversation_id
        )

    def add_message(
        self,
        conversation_id,
        role,
        message
    ):

        conversation = self.get(
            conversation_id
        )

        if not conversation:
            return None

        cleaned_message = message.strip()

        # ---------------------------------------------
        # MERCHANT MESSAGE TRACKING
        # ---------------------------------------------

        if role == "merchant":

            conversation["merchant_turns"] += 1

            last_merchant_message = (
                conversation.get(
                    "last_merchant_message"
                )
            )

            if (
                last_merchant_message
                and last_merchant_message.lower()
                == cleaned_message.lower()
            ):
                conversation["repeated_count"] += 1

            else:
                conversation["repeated_count"] = 1

            conversation[
                "last_merchant_message"
            ] = cleaned_message


        # ---------------------------------------------
        # STORE MESSAGE
        # ---------------------------------------------

        conversation["messages"].append({
            "role": role,
            "message": cleaned_message
        })

        conversation["turn_number"] += 1

        return conversation

    def end(self, conversation_id):

        conversation = self.get(
            conversation_id
        )

        if conversation:
            conversation["status"] = "ended"

    def update_intent(
        self,
        conversation_id,
        intent
    ):

        conversation = self.get(
            conversation_id
        )

        if conversation:
            conversation["intent"] = intent

            # Reset repeated-message tracking when
            # merchant changes intent.
            conversation["repeated_count"] = 0
            conversation["last_merchant_message"] = None