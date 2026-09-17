import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


# ============================================================
# ENVIRONMENT & SECRETS
# ============================================================

load_dotenv()


def get_secret(name: str, default=None):
    """
    Read configuration from Streamlit Secrets when deployed.
    Fall back to environment variables for local development.
    """

    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return os.getenv(name, default)


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

GEMINI_MODEL = get_secret(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

# Backup model used when the primary model is temporarily unavailable
# or when the primary model reaches its quota.
GEMINI_FALLBACK_MODEL = "gemini-3.7-flash"


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# CONVERSATION CONTEXT
# ============================================================

@dataclass
class ConversationContext:

    user_id: str = "akshaya"

    last_intent: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    history: List[Dict[str, str]] = field(
        default_factory=list
    )


# ============================================================
# WORKFLOW LOGS
# ============================================================

WORKFLOW_LOGS = []


def add_workflow_log(
    action: str,
    status: str = "Completed",
    details: str = ""
):

    WORKFLOW_LOGS.append({

        "action": action,

        "status": status,

        "details": details

    })


# ============================================================
# WORKBUDDY KNOWLEDGE
# ============================================================

WORKBUDDY_KNOWLEDGE = {

    "leave_policy": """
    Leave Policy:
    - Employees should inform their manager before taking planned leave.
    - Leave requests should follow the organization's internal leave process.
    - For planned personal events, employees should communicate the expected dates
      and reason to their manager.
    - Emergency or unexpected leave should be communicated as soon as possible.
    - WorkBuddy provides guidance and drafting assistance but does not approve leave
      or calculate leave balances.
    """,

    "attendance_policy": """
    Attendance Guidance:
    - Employees are expected to follow their organization's working hours.
    - If an employee expects to be absent or late, they should communicate with
      their manager according to company procedures.
    - WorkBuddy can explain general attendance guidance but cannot modify attendance
      records.
    """,

    "work_from_home": """
    Work From Home Guidance:
    - Employees should follow the organization's WFH policy and approval process.
    - Planned WFH should normally be communicated to the manager in advance.
    - WorkBuddy can help explain the process or draft a communication.
    """,

    "it_access": """
    IT Access Guidance:
    - Employees requiring access to workplace tools should raise an access request
      through the organization's approved IT process.
    - Examples may include Jira, GitHub, Microsoft Teams, VPN, email systems,
      development environments, or other internal tools.
    - WorkBuddy can explain the process and draft an access request.
    - WorkBuddy does not actually grant permissions.
    """,

    "it_support": """
    IT Support Guidance:
    - For technical problems, employees should describe the problem, affected
      application/device, and any error message.
    - WorkBuddy can provide troubleshooting guidance.
    - If the issue requires the IT team, WorkBuddy can help draft a support ticket.
    """,

    "onboarding": """
    Onboarding Guidance:
    - New employees generally need to complete organizational, HR, security,
      and technical onboarding activities.
    - WorkBuddy can explain onboarding steps and help prepare questions or
      communications.
    - WorkBuddy does not mark onboarding tasks as officially completed.
    """,

    "workplace_communication": """
    Workplace Communication:
    - WorkBuddy can draft professional emails, messages, requests, explanations,
      and letters.
    - The user can ask for formal, casual, concise, polite, or detailed versions.
    """
}


# ============================================================
# STRUCTURED LLM RESPONSE
# ============================================================

class WorkBuddyResponse(BaseModel):

    agent: str = Field(
        description="The WorkBuddy area handling the request."
    )

    intent: str = Field(
        description="The user's main intent."
    )

    response: str = Field(
        description="Natural language response to the employee."
    )

    actions: List[str] = Field(
        default_factory=list,
        description="Helpful next actions WorkBuddy can suggest."
    )

    knowledge_used: List[str] = Field(
        default_factory=list,
        description="Knowledge categories used to answer."
    )


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are WorkBuddy, an AI-powered workplace copilot.

Your purpose is to help employees understand workplace processes and communicate
with HR and IT teams.

You are conversational and should understand natural language rather than relying
on keywords.

IMPORTANT BEHAVIOR:

1. Understand the employee's situation.

Example:

Employee:
"I have a family event next week."

You should understand that the employee may be talking about planned leave.

A helpful response could explain the relevant leave guidance and offer:
"Would you like me to draft a leave email to your manager?"

Do NOT simply ask the user to type "leave".

2. Maintain conversational context.

If the user says:
"Yes, make it formal."

Understand that they are referring to the previous request.

3. You can help with:
- HR policies
- Leave guidance
- Attendance guidance
- WFH guidance
- IT support
- IT access guidance
- Onboarding guidance
- Workplace questions
- Professional emails
- Leave letters
- IT support messages
- Access request drafts

4. Do NOT behave like a traditional leave management system.

You must NOT:
- calculate leave balances
- approve leave
- reject leave
- modify attendance
- grant IT permissions
- mark onboarding tasks as officially completed
- pretend that an action happened when it did not

5. You may suggest what the employee should do next.

For example:
- Contact the manager
- Raise an IT request
- Provide an error message
- Prepare an email
- Follow the organization's process

6. When drafting an email or letter:
- Make it professional
- Keep it natural
- Include placeholders where information is missing
- Do not invent employee-specific facts

7. Use the provided WorkBuddy knowledge when relevant.

Do not invent company-specific policies that are not provided.

8. If the user asks something unrelated to HR, IT, onboarding, or workplace
assistance, politely explain that WorkBuddy is designed for workplace assistance
and still try to help if the request is reasonably related.

9. Keep responses clear and human.
Avoid unnecessary technical explanations.

10. Never claim that IBM watsonx Orchestrate is actively executing a workflow
unless a real IBM integration has been implemented.
"""


# ============================================================
# FORMAT KNOWLEDGE
# ============================================================

def format_knowledge() -> str:

    knowledge_text = ""

    for category, content in WORKBUDDY_KNOWLEDGE.items():

        knowledge_text += (
            f"\n--- {category.upper()} ---\n"
            f"{content}\n"
        )

    return knowledge_text


# ============================================================
# FORMAT CONVERSATION HISTORY
# ============================================================

def format_history(
    history: List[Dict[str, str]]
) -> str:

    if not history:
        return "No previous conversation."

    recent_history = history[-8:]

    formatted = []

    for message in recent_history:

        role = message.get(
            "role",
            "user"
        )

        content = message.get(
            "content",
            ""
        )

        formatted.append(
            f"{role.upper()}: {content}"
        )

    return "\n".join(formatted)


# ============================================================
# LLM CALL
# ============================================================

def ask_workbuddy_llm(
    user_message: str,
    context: ConversationContext
) -> WorkBuddyResponse:

    if client is None:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    prompt = f"""
WORKBUDDY KNOWLEDGE:

{format_knowledge()}


PREVIOUS CONVERSATION:

{format_history(context.history)}


CURRENT EMPLOYEE MESSAGE:

{user_message}


Respond as WorkBuddy.

Understand the intent from the meaning of the message and the conversation
context.

If useful, suggest one or more practical next actions.

If the user appears to need an email, letter, request, or message, proactively
offer to draft it.
"""

    # ========================================================
    # PRIMARY MODEL + FALLBACK MODEL
    # ========================================================

    models_to_try = [
        GEMINI_MODEL,
        GEMINI_FALLBACK_MODEL
    ]

    last_error = None

    for model_index, model_name in enumerate(models_to_try):

        is_fallback_model = model_index > 0

        # ----------------------------------------------------
        # Log which model is being attempted
        # ----------------------------------------------------

        if is_fallback_model:

            add_workflow_log(
                action=f"Switching to fallback model: {model_name}",
                status="Started",
                details=(
                    f"Primary model {GEMINI_MODEL} was unavailable "
                    f"or reached its quota."
                )
            )

        else:

            add_workflow_log(
                action=f"Trying primary model: {model_name}",
                status="Started",
                details="Starting Gemini response generation."
            )

        for attempt in range(3):

            try:

                response = client.models.generate_content(

                    model=model_name,

                    contents=prompt,

                    config=types.GenerateContentConfig(

                        system_instruction=SYSTEM_INSTRUCTION,

                        response_mime_type="application/json",

                        response_schema=WorkBuddyResponse

                    )

                )

                if response.parsed is None:

                    raise RuntimeError(
                        f"Gemini model {model_name} returned "
                        "an empty or invalid response."
                    )

                # ------------------------------------------------
                # Successful response
                # ------------------------------------------------

                add_workflow_log(
                    action=f"LLM response generated: {model_name}",
                    status="Completed",
                    details=(
                        f"WorkBuddy successfully received a response "
                        f"from {model_name}."
                    )
                )

                return response.parsed

            except Exception as e:

                last_error = e

                error_message = str(e)

                # ------------------------------------------------
                # Detect temporary capacity errors
                # ------------------------------------------------

                is_503_error = (
                    "503" in error_message
                    or "UNAVAILABLE" in error_message
                )

                # ------------------------------------------------
                # Detect quota / rate-limit errors
                # ------------------------------------------------

                is_429_error = (
                    "429" in error_message
                    or "RESOURCE_EXHAUSTED" in error_message
                    or "quota" in error_message.lower()
                )

                # ------------------------------------------------
                # Log the model-specific failure
                # ------------------------------------------------

                add_workflow_log(
                    action=f"Model error: {model_name}",
                    status="Failed",
                    details=(
                        f"Attempt {attempt + 1}/3 | "
                        f"Error: {error_message}"
                    )
                )

                # ------------------------------------------------
                # Retry temporary 503 errors
                # ------------------------------------------------

                if (
                    is_503_error
                    and attempt < 2
                ):

                    add_workflow_log(
                        action=f"Retrying {model_name}",
                        status="Retrying",
                        details=(
                            f"Temporary 503 capacity error. "
                            f"Retry {attempt + 2}/3 scheduled."
                        )
                    )

                    time.sleep(2 ** attempt)

                    continue

                # ------------------------------------------------
                # 503 after retries:
                # move to fallback model
                # ------------------------------------------------

                if (
                    is_503_error
                    and attempt == 2
                ):

                    add_workflow_log(
                        action=f"Fallback triggered from {model_name}",
                        status="Fallback",
                        details=(
                            "Primary model remained unavailable "
                            "after 3 attempts."
                        )
                    )

                    break

                # ------------------------------------------------
                # 429 quota error:
                # immediately move to fallback model
                # ------------------------------------------------

                if is_429_error:

                    add_workflow_log(
                        action=f"Quota fallback triggered from {model_name}",
                        status="Fallback",
                        details=(
                            "Quota or rate-limit error detected. "
                            "Moving to the next available model."
                        )
                    )

                    break

                # ------------------------------------------------
                # Do not hide other API/configuration errors.
                # ------------------------------------------------

                raise

    # ========================================================
    # ALL MODELS FAILED
    # ========================================================

    if last_error is not None:

        add_workflow_log(
            action="All Gemini models failed",
            status="Failed",
            details=(
                "Both the primary and fallback models were "
                "unable to generate a response."
            )
        )

        raise last_error

    raise RuntimeError(
        "No Gemini model was available."
    )


# ============================================================
# FALLBACK RESPONSE
# ============================================================

def fallback_response(
    user_message: str
):

    return WorkBuddyResponse(

        agent="🤖 WorkBuddy",

        intent="general_workplace_assistance",

        response=(
            "I'm having trouble connecting to the AI service right now. "
            "Please try again in a moment."
        ),

        actions=[
            "Try the message again"
        ],

        knowledge_used=[]

    )


# ============================================================
# MAIN WORKBUDDY HANDLER
# ============================================================

def handle_user_message(
    user_message: str,
    context: ConversationContext
):

    user_message = user_message.strip()

    if not user_message:

        return (

            "Tell me what you need help with, "
            "and I'll do my best to assist.",

            context,

            {

                "agent": "🤖 WorkBuddy",

                "intent": "empty_message",

                "actions": []

            }

        )

    # --------------------------------------------------------
    # Save user message
    # --------------------------------------------------------

    context.history.append({

        "role": "user",

        "content": user_message

    })

    try:

        result = ask_workbuddy_llm(

            user_message,

            context

        )

        # ----------------------------------------------------
        # Update context
        # ----------------------------------------------------

        context.last_intent = result.intent

        context.metadata = {

            "agent": result.agent,

            "knowledge_used": result.knowledge_used

        }

        # ----------------------------------------------------
        # Save assistant response
        # ----------------------------------------------------

        context.history.append({

            "role": "assistant",

            "content": result.response

        })

        # ----------------------------------------------------
        # Workflow logging
        # ----------------------------------------------------

        add_workflow_log(

            action=f"LLM understood: {result.intent}",

            status="Completed",

            details=(

                f"Agent: {result.agent} | "

                f"Knowledge: "
                f"{', '.join(result.knowledge_used)}"

            )

        )

        return (

            result.response,

            context,

            {

                "agent": result.agent,

                "intent": result.intent,

                "actions": result.actions

            }

        )

    except Exception as e:

        error_message = str(e)

        add_workflow_log(

            action="LLM response generation",

            status="Failed",

            details=error_message

        )

        fallback = fallback_response(

            user_message

        )

        context.history.append({

            "role": "assistant",

            "content": fallback.response

        })

        return (

            fallback.response,

            context,

            {

                "agent": fallback.agent,

                "intent": fallback.intent,

                "actions": fallback.actions

            }

        )
