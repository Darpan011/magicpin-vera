from fastapi import FastAPI
from datetime import datetime
import json
import os
import time
import uuid

from context_store import ContextStore
from decision_engine import DecisionEngine
from context_resolver import ContextResolver
from composer import VeraComposer
from llm_composer import LLMComposer
from validator import MessageValidator
from conversation_store import ConversationStore
from conversation_handler import ConversationHandler


app = FastAPI(title="Magicpin Vera")


# =========================================================
# INITIALIZE COMPONENTS
# =========================================================

store = ContextStore()
decision_engine = DecisionEngine()
resolver = ContextResolver(store)
composer = VeraComposer()
llm_composer = LLMComposer()
validator = MessageValidator()

conversation_store = ConversationStore()
conversation_handler = ConversationHandler()

START_TIME = time.time()


# =========================================================
# MESSAGE ENCODING CLEANUP
# =========================================================

def clean_message_encoding(text):
    if not text:
        return text

    replacements = {
        # Rupee / currency mojibake
        "â¹": "₹",
        "â‚¹": "₹",
        "â\x82¹": "₹",
        "Â₹": "₹",

        # UTF-8 punctuation mojibake
        "â€“": "–",
        "â€”": "—",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€¦": "…",

        # Remove stray encoding marker
        "Â": "",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Fix corrupted punctuation between words
    text = text.replace("â shall", " — shall")
    text = text.replace("âshall", " — shall")

    # Fix common word concatenation
    text = text.replace("volumeand", "volume and")
    text = text.replace("handlelarge", "handle large")

    # Normalize accidental double spaces
    while "  " in text:
        text = text.replace("  ", " ")

    return text.strip()


# =========================================================
# DATASET LOADING
# =========================================================

def load_dataset_into_store():

    base_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "dataset",
        "expanded"
    )

    scope_map = {
        "categories": "category",
        "merchants": "merchant",
        "customers": "customer",
        "triggers": "trigger",
    }

    total = 0

    for folder_name, scope_name in scope_map.items():

        folder = os.path.join(
            base_dir,
            folder_name
        )

        if not os.path.isdir(folder):

            print(
                f"Skipping {folder_name}: folder not found"
            )

            continue

        files = sorted(
            filename
            for filename in os.listdir(folder)
            if filename.lower().endswith(".json")
        )

        print(
            f"Loading {scope_name}: "
            f"{len(files)} contexts..."
        )

        for filename in files:

            file_path = os.path.join(
                folder,
                filename
            )

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    payload = json.load(f)

                # IMPORTANT:
                # The dataset's filename is the context ID.
                # This matches the original working
                # load_dataset.py logic.

                context_id = os.path.splitext(
                    filename
                )[0]

                accepted, reason = store.store(
                    scope_name,
                    context_id,
                    1,
                    payload
                )

                if accepted:

                    total += 1

                else:

                    print(
                        f"ERROR {scope_name} "
                        f"{context_id}: {reason}"
                    )

            except Exception as e:

                print(
                    f"ERROR loading "
                    f"{scope_name} "
                    f"{filename}: {e}"
                )

        print(
            f"{scope_name}: done"
        )

    print(
        f"\nDataset loading complete: "
        f"{total} contexts"
    )

    print(
        "Context counts:",
        store.counts()
    )


# =========================================================
# FASTAPI STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():

    print(
        "Initializing Magicpin Vera..."
    )

    load_dataset_into_store()

    print(
        "Vera startup complete."
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/v1/healthz")
def healthz():

    return {
        "status": "ok",
        "uptime_seconds": int(
            time.time() - START_TIME
        ),
        "contexts_loaded": store.counts()
    }


# =========================================================
# METADATA
# =========================================================

@app.get("/v1/metadata")
def metadata():

    return {
        "team_name": "YOUR_TEAM_NAME",
        "team_members": [
            "YOUR_NAME"
        ],
        "model": os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite"
        ),
        "approach": (
            "Stateful AI merchant assistant"
        ),
        "contact_email": "YOUR_EMAIL",
        "version": "0.1.0",
        "submitted_at": datetime.utcnow().isoformat()
    }


# =========================================================
# CONTEXT INGESTION
# =========================================================

@app.post("/v1/context")
def receive_context(payload: dict):

    scope = payload.get("scope")
    context_id = payload.get("context_id")
    version = payload.get("version")
    context_data = payload.get("payload")

    if (
        not scope
        or not context_id
        or version is None
        or context_data is None
    ):

        return {
            "accepted": False,
            "reason": "invalid_payload"
        }

    accepted, reason = store.store(
        scope,
        context_id,
        version,
        context_data
    )

    if not accepted:

        return {
            "accepted": False,
            "reason": reason,
            "current_version": (
                store.versions
                .get(scope, {})
                .get(context_id)
            )
        }

    return {
        "accepted": True,
        "ack_id": (
            f"ack_{scope}_{context_id}_{version}"
        ),
        "stored_at": datetime.utcnow().isoformat()
    }


# =========================================================
# TICK
# Generate new outbound merchant actions
# =========================================================

@app.post("/v1/tick")
def tick(payload: dict):

    available_triggers = payload.get(
        "available_triggers",
        []
    )

    actions = []

    for trigger in available_triggers:

        # -------------------------------------------------
        # Resolve trigger ID to stored trigger context
        # -------------------------------------------------

        if isinstance(trigger, dict):

            trigger_ref = trigger.get(
                "trigger_id",
                trigger.get("id")
            )

            # If only an ID/reference was supplied, load the
            # complete trigger from the ContextStore.

            if (
                trigger_ref
                and not trigger.get("merchant_id")
                and not trigger.get("kind")
            ):

                stored_trigger = store.get(
                    "trigger",
                    trigger_ref
                )

                if stored_trigger:

                    trigger = dict(stored_trigger)

                    # Keep the API's trigger_id convention.
                    trigger["trigger_id"] = trigger_ref

        # -------------------------------------------------
        # Validate trigger object
        # -------------------------------------------------

        if not isinstance(
            trigger,
            dict
        ):

            print(
                "Skipping invalid trigger:",
                trigger
            )

            continue

        # -------------------------------------------------
        # 1. ROUTE TRIGGER
        # -------------------------------------------------

        routing = decision_engine.route(
            trigger
        )

        strategy = routing["strategy"]

        # -------------------------------------------------
        # 2. RESOLVE CONTEXT
        # -------------------------------------------------

        context = resolver.resolve(
            trigger
        )

        # Merchant context is required

        if not context["merchant"]:

            print(
                "Skipping trigger because merchant "
                "context was not found:",
                trigger.get("trigger_id")
            )

            continue

        # -------------------------------------------------
        # 3. GENERATE MESSAGE USING GEMINI
        # -------------------------------------------------

        print("DEBUG: About to call Gemini", flush=True)

        message = llm_composer.compose(
            context,
            strategy
        )

        print("DEBUG: Gemini returned", flush=True)

        # -------------------------------------------------
        # 4. FALLBACK TO DETERMINISTIC COMPOSER
        # -------------------------------------------------

        if message is None:

            message = composer.compose(
                context,
                strategy
            )

        # -------------------------------------------------
        # 5. VALIDATE MESSAGE
        # -------------------------------------------------

        valid, reason = validator.validate(
            message,
            context,
            strategy
        )

        # -------------------------------------------------
        # 6. FALLBACK IF VALIDATION FAILS
        # -------------------------------------------------

        if not valid:

            print(
                f"LLM message rejected: {reason}"
            )

            message = composer.compose(
                context,
                strategy
            )

        # -------------------------------------------------
        # CLEAN MESSAGE ENCODING
        # -------------------------------------------------

        if message.get("body"):

            message["body"] = clean_message_encoding(
                message["body"]
            )

        # -------------------------------------------------
        # 7. GET TRIGGER ID
        # -------------------------------------------------

        trigger_id = trigger.get(
            "trigger_id",
            trigger.get(
                "id",
                "unknown"
            )
        )

        # -------------------------------------------------
        # 8. CREATE UNIQUE CONVERSATION ID
        # -------------------------------------------------

        conversation_id = (
            f"conv_{trigger_id}_"
            f"{uuid.uuid4().hex[:8]}"
        )

        # -------------------------------------------------
        # 9. CREATE CONVERSATION STATE
        # -------------------------------------------------

        conversation_store.create(
            conversation_id=conversation_id,
            merchant_id=trigger.get(
                "merchant_id"
            ),
            customer_id=trigger.get(
                "customer_id"
            ),
            trigger_id=trigger_id,
            strategy=strategy
        )

        # -------------------------------------------------
        # 10. STORE VERA'S INITIAL MESSAGE
        # -------------------------------------------------

        conversation_store.add_message(
            conversation_id,
            "vera",
            message["body"]
        )

        # -------------------------------------------------
        # 11. ADD ACTION
        # -------------------------------------------------

        actions.append({
            "conversation_id": conversation_id,

            "merchant_id": trigger.get(
                "merchant_id"
            ),

            "customer_id": trigger.get(
                "customer_id"
            ),

            "trigger_id": trigger_id,

            "action": "send",

            **message
        })

    return {
        "actions": actions
    }


# =========================================================
# REPLY
# Continue an existing WhatsApp conversation
# =========================================================

@app.post("/v1/reply")
def reply(payload: dict):

    # -------------------------------------------------
    # 1. READ REQUEST
    # -------------------------------------------------

    conversation_id = payload.get(
        "conversation_id"
    )

    merchant_id = payload.get(
        "merchant_id"
    )

    customer_id = payload.get(
        "customer_id"
    )

    message = payload.get(
        "message",
        ""
    ).strip()

    # -------------------------------------------------
    # 2. BASIC VALIDATION
    # -------------------------------------------------

    if (
        not conversation_id
        or not message
    ):

        return {
            "action": "end",
            "rationale": (
                "Missing conversation_id or message."
            )
        }

    # -------------------------------------------------
    # 3. GET CONVERSATION
    # -------------------------------------------------

    conversation = conversation_store.get(
        conversation_id
    )

    # -------------------------------------------------
    # 4. RECOVER CONVERSATION IF NECESSARY
    # -------------------------------------------------

    if not conversation:

        conversation = conversation_store.create(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id
        )

    # -------------------------------------------------
    # 5. CHECK IF ALREADY ENDED
    # -------------------------------------------------

    if conversation["status"] == "ended":

        return {
            "action": "end",
            "rationale": (
                "Conversation already ended."
            )
        }

    # -------------------------------------------------
    # 6. STORE MERCHANT MESSAGE
    # -------------------------------------------------

    conversation_store.add_message(
        conversation_id,
        "merchant",
        message
    )

    # -------------------------------------------------
    # 7. CLASSIFY INTENT
    # -------------------------------------------------

    intent = conversation_handler.classify(
        message,
        conversation
    )

    # -------------------------------------------------
    # 8. STOP / NOT INTERESTED
    # -------------------------------------------------

    if intent == "stop":

        conversation_store.end(
            conversation_id
        )

        return {
            "action": "end",
            "rationale": (
                "Merchant requested to stop or declined."
            )
        }

    # -------------------------------------------------
    # 9. AUTO-REPLY DETECTION
    # -------------------------------------------------

    if intent == "auto_reply":

        conversation_store.end(
            conversation_id
        )

        return {
            "action": "end",
            "rationale": (
                "Repeated automated response detected."
            )
        }

    # -------------------------------------------------
    # 10. INTENT TRANSITIONS
    # -------------------------------------------------

    if intent == "offer_drafting":

        conversation_store.update_intent(
            conversation_id,
            "offer_drafting"
        )

    elif intent == "profile_help":

        conversation_store.update_intent(
            conversation_id,
            "profile_help"
        )

    # -------------------------------------------------
    # 11. OFF-TOPIC REQUEST
    # -------------------------------------------------

    elif intent == "off_topic_gst":

        response = {
            "body": (
                "I can help with your Magicpin listing, "
                "offers and merchant growth tasks. "
                "For GST filing, you'll need a tax professional."
            ),
            "cta": None,
            "send_as": "freeform",
            "suppression_key": None,
            "rationale": (
                "Off-topic request handled with "
                "a graceful boundary."
            )
        }

        response["body"] = clean_message_encoding(
            response["body"]
        )

        conversation_store.add_message(
            conversation_id,
            "vera",
            response["body"]
        )

        return {
            "action": "send",
            **response
        }

    # -------------------------------------------------
    # 12. RESOLVE CURRENT CONTEXT
    # -------------------------------------------------

    trigger_id = conversation.get(
        "trigger_id"
    )

    merchant_id = conversation.get(
        "merchant_id"
    )

    customer_id = conversation.get(
        "customer_id"
    )

    trigger = (
        store.get(
            "trigger",
            trigger_id
        )
        if trigger_id
        else {}
    )

    # -------------------------------------------------
    # 13. FALLBACK TRIGGER
    # -------------------------------------------------

    if not trigger:

        trigger = {
            "trigger_id": trigger_id,

            "merchant_id": merchant_id,

            "customer_id": customer_id
        }

    # -------------------------------------------------
    # 14. RESOLVE CONTEXT
    # -------------------------------------------------

    context = resolver.resolve(
        trigger
    )

    # -------------------------------------------------
    # 15. DETERMINE CURRENT STRATEGY
    # -------------------------------------------------

    strategy = (
        conversation.get("intent")
        or conversation.get("strategy")
        or "general_merchant_assistance"
    )

    # -------------------------------------------------
    # 16. GEMINI CONTINUATION
    # -------------------------------------------------

    response = (
        llm_composer.continue_conversation(
            context,
            strategy,
            conversation
        )
    )

    # -------------------------------------------------
    # 17. FALLBACK IF GEMINI FAILS
    # -------------------------------------------------

    if response is None:

        response = {

            "body": (
                "Got it. I can help with that. "
                "What would you like me to work on first?"
            ),

            "cta": "YES",

            "send_as": "freeform",

            "suppression_key": None,

            "rationale": (
                "Fallback conversation response."
            )
        }

    # -------------------------------------------------
    # 18. VALIDATE RESPONSE
    # -------------------------------------------------

    valid, reason = validator.validate(
        response,
        context,
        strategy
    )

    # -------------------------------------------------
    # 19. FALLBACK IF VALIDATION FAILS
    # -------------------------------------------------

    if not valid:

        print(
            f"Conversation response rejected: {reason}"
        )

        response = {

            "body": (
                "Got it. I can help with the next step. "
                "Want me to continue?"
            ),

            "cta": "YES",

            "send_as": "freeform",

            "suppression_key": None,

            "rationale": (
                "Fallback after validation failure: "
                f"{reason}"
            )
        }

    # -------------------------------------------------
    # 20. CLEAN MESSAGE ENCODING
    # -------------------------------------------------

    if response.get("body"):

        response["body"] = clean_message_encoding(
            response["body"]
        )

    # -------------------------------------------------
    # 21. STORE VERA'S RESPONSE
    # -------------------------------------------------

    conversation_store.add_message(
        conversation_id,
        "vera",
        response["body"]
    )

    # -------------------------------------------------
    # 22. RETURN RESPONSE
    # -------------------------------------------------

    return {
        "action": "send",
        **response
    }