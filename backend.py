# backend.py
# WorkBuddy — LLM-Powered Employee Copilot
#
# Core idea:
# User message
#      ↓
# Gemini LLM
#      ↓
# Understand intent + context
#      ↓
# Ground response in WorkBuddy knowledge
#      ↓
# Generate helpful response
#      ↓
# Suggest useful next actions
#
# No SQL / no leave-balance management / no approval system.

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
import datetime
import json
import os
import uuid

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from google import genai
from google.genai import types


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# WORKFLOW LOGS
# ============================================================

WORKFLOW_LOGS: List[Dict[str, Any]] = []


def make_id(prefix: str) -> str:
    """Create a short reference ID."""
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def log_workflow(
    agent: str,
    skill: str,
    status: str,
    ref_id: str | None = None,
    details: str | None = None,
):
    """
    Record an execution event.

    These logs are displayed in the WorkBuddy dashboard
    to visualize the agentic workflow.
    """

    WORKFLOW_LOGS.append(
        {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "agent": agent,
            "skill": skill,
            "status": status,
            "ref_id": ref_id,
            "details": details,
        }
    )


# ============================================================
# CONVERSATION CONTEXT
# ============================================================

@dataclass
class ConversationContext:

    user_id: str = "akshaya"

    last_intent: str | None = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # Conversation history used by the LLM.
    history: List[Dict[str, str]] = field(
        default_factory=list
    )


# ============================================================
# WORKBUDDY KNOWLEDGE BASE
# ============================================================
#
# This is intentionally lightweight.
#
# It is NOT a database.
#
# Later, this can be replaced with:
# - company documents
# - Cloudant
# - vector database
# - RAG
# - IBM watsonx knowledge sources
#
# For now, it gives the LLM grounded company-style
# information instead of allowing it to invent policies.
# ============================================================

WORKBUDDY_KNOWLEDGE = {

    "leave_policy": {
        "title": "Leave Policy",
        "content": """
Planned leave should normally be requested in advance according
to the organization's leave process.

Employees should communicate the requested dates and reason
appropriately to their reporting manager.

For urgent or emergency situations, employees should contact
their reporting manager as soon as possible.

Leave requests remain subject to the organization's applicable
approval process.
"""
    },

    "attendance_policy": {
        "title": "Attendance Policy",
        "content": """
Employees are expected to follow the organization's working
hours and attendance requirements.

If an employee expects to be absent or delayed, they should
inform their reporting manager according to the applicable
workplace process.

For attendance-related concerns, employees can contact HR
or their reporting manager for clarification.
"""
    },

    "work_from_home": {
        "title": "Work From Home Guidance",
        "content": """
Work-from-home arrangements depend on organizational policy,
team requirements, role requirements, and manager approval.

Employees should follow the applicable internal process when
requesting remote work.
"""
    },

    "it_access": {
        "title": "IT Access Guidance",
        "content": """
Employees who require access to workplace tools such as
Jira, Salesforce, GitHub, VPN, email systems, or analytics
platforms should follow the organization's IT access process.

Requests should normally include the employee's role,
required application, and business justification when needed.
"""
    },

    "it_support": {
        "title": "IT Support Guidance",
        "content": """
For technical problems, employees should first describe the
issue clearly, including the affected application or device.

Depending on the problem, IT support may require details such
as screenshots, error messages, device information, or the
time when the issue occurred.
"""
    },

    "onboarding": {
        "title": "Employee Onboarding Guidance",
        "content": """
New employees may need to complete onboarding documentation,
receive their device, obtain required system access, configure
VPN or workplace tools, and connect with their reporting
manager and team.

The exact onboarding requirements depend on the employee's
role and organization.
"""
    },

    "workplace_communication": {
        "title": "Workplace Communication Guidance",
        "content": """
Professional workplace communication should normally be clear,
concise, respectful, and include the relevant request,
dates, context, and any action required from the recipient.
"""
    },

}


# ============================================================
# LLM RESPONSE SCHEMA
# ============================================================

class WorkBuddyResponse(BaseModel):

    agent: str = Field(
        description=(
            "The most appropriate WorkBuddy area handling "
            "the request. Use one of: HR Agent, IT Agent, "
            "Onboarding Agent, General Assistant."
        )
    )

    intent: str = Field(
        description=(
            "A concise description of the user's intent, "
            "such as leave_guidance, policy_question, "
            "email_drafting, it_support, it_access, "
            "onboarding_guidance, general_workplace_help."
        )
    )

    response: str = Field(
        description=(
            "The complete natural-language response that "
            "should be shown to the employee."
        )
    )

    actions: List[str] = Field(
        default_factory=list,
        description=(
            "Useful next-step options WorkBuddy can offer "
            "the employee. Keep them concise."
        )
    )

    knowledge_used: List[str] = Field(
        default_factory=list,
        description=(
            "Names of the WorkBuddy knowledge topics used "
            "to answer the request."
        )
    )


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are WorkBuddy, an intelligent workplace employee copilot.

Your role is to help employees with everyday HR, IT,
onboarding, workplace-policy, and professional-communication
questions.

You are conversational and proactive.

IMPORTANT BEHAVIOR:

1. UNDERSTAND NATURAL LANGUAGE

Do not require users to use commands such as:
"check leave balance"
"request access"
"start onboarding"

Understand normal human statements.

Example:

User:
"I have a family event next week."

Understand that the user may be seeking leave guidance even
though they did not explicitly say "leave".

2. DO NOT TURN WORKBUDDY INTO A LEAVE MANAGEMENT SYSTEM

Do NOT calculate leave balances.

Do NOT approve or reject leave.

Do NOT invent employee records.

Do NOT pretend to submit an official leave request unless
a real action tool has been implemented.

Instead, provide guidance and offer useful help such as:

- explaining the relevant policy
- drafting a leave application
- formatting an email to a manager
- preparing a formal letter
- helping the user communicate the request

3. USE PROVIDED KNOWLEDGE

When a workplace policy is relevant, use the supplied
WorkBuddy knowledge.

Do not invent company-specific policies.

If the knowledge provided does not contain an answer,
clearly say that the employee should confirm the exact
policy with HR or the appropriate internal team.

4. BE PROACTIVE

After answering, suggest one or two useful next steps.

For example:

"Would you like me to draft a formal email to your manager?"

or:

"I can also format this as a leave application letter
if you'd like."

Do not overwhelm the user with a huge menu.

5. DOCUMENT GENERATION

If the user asks for an email, letter, message,
application, checklist, or similar document, generate it
directly.

Use professional but natural language.

6. FOLLOW-UP CONTEXT

Use the previous conversation when answering follow-up
questions.

Example:

User:
"I have a family event next week."

Assistant:
"You can apply for leave according to the applicable
leave policy. Would you like an email format?"

User:
"Yes, make it formal."

Understand that "it" refers to the leave email.

7. HR

Help with:
- leave guidance
- attendance guidance
- HR policies
- workplace questions
- communication with managers
- HR-related document drafting

8. IT

Help with:
- IT support guidance
- software access guidance
- troubleshooting
- IT request drafting
- access-request communication

Do not claim that access was actually granted unless a real
IT tool has been connected.

9. ONBOARDING

Help with:
- onboarding checklists
- new-joiner preparation
- workplace setup guidance
- required tools
- manager/team communication
- onboarding document drafting

Do not claim that an employee account, laptop, VPN, or access
was actually created.

10. GENERAL QUESTIONS

For general workplace questions, behave like a helpful
employee copilot.

11. TONE

Be friendly, professional, concise, and useful.

Do not sound like a rigid chatbot.

12. IBM WATSONX ORCHESTRATE

WorkBuddy is conceptually designed around agentic orchestration
and digital skills similar to an IBM watsonx Orchestrate setup.

Do not falsely claim that a live watsonx Orchestrate workflow
was executed unless an actual integration has been connected.
"""


# ============================================================
# KNOWLEDGE CONTEXT BUILDER
# ============================================================

def build_knowledge_context() -> str:
    """
    Convert the local WorkBuddy knowledge base into a compact
    context block for the LLM.
    """

    sections = []

    for key, article in WORKBUDDY_KNOWLEDGE.items():

        sections.append(
            f"""
### {article['title']}
Knowledge ID: {key}

{article['content'].strip()}
"""
        )

    return "\n".join(sections)


# ============================================================
# CONVERSATION HISTORY
# ============================================================

def build_conversation_context(
    ctx: ConversationContext,
) -> str:

    if not ctx.history:
        return "No previous conversation."

    recent_history = ctx.history[-10:]

    lines = []

    for item in recent_history:

        role = item.get(
            "role",
            "user"
        )

        content = item.get(
            "content",
            ""
        )

        lines.append(
            f"{role.upper()}: {content}"
        )

    return "\n".join(lines)


# ============================================================
# GEMINI CALL
# ============================================================

def generate_llm_response(
    message: str,
    ctx: ConversationContext,
) -> WorkBuddyResponse:

    if client is None:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Create a .env file and add GEMINI_API_KEY."
        )


    knowledge_context = build_knowledge_context()

    conversation_context = build_conversation_context(
        ctx
    )


    prompt = f"""
{SYSTEM_INSTRUCTION}

============================================================
WORKBUDDY KNOWLEDGE
============================================================

{knowledge_context}

============================================================
PREVIOUS CONVERSATION
============================================================

{conversation_context}

============================================================
CURRENT USER MESSAGE
============================================================

{message}

============================================================
TASK
============================================================

Understand what the employee means.

Use relevant WorkBuddy knowledge when appropriate.

Respond naturally.

If the user appears to need a workplace action but no real
action tool exists, provide guidance and offer to help prepare
the required communication rather than pretending the action
was completed.

Return the required structured response.
"""


    log_workflow(
        agent="WorkBuddy",
        skill="UnderstandUserRequest",
        status="Started",
        details="Sending natural-language request to LLM",
    )


    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=WorkBuddyResponse,
            temperature=0.7,
        ),
    )


    if not response.text:
        raise RuntimeError(
            "The LLM returned an empty response."
        )


    result = WorkBuddyResponse.model_validate_json(
        response.text
    )


    log_workflow(
        agent=result.agent,
        skill="GenerateWorkplaceResponse",
        status="Completed",
        details=(
            f"Intent: {result.intent}; "
            f"Knowledge: {', '.join(result.knowledge_used) or 'None'}"
        ),
    )


    return result


# ============================================================
# FALLBACK RESPONSE
# ============================================================

def fallback_response(
    message: str,
) -> WorkBuddyResponse:

    """
    Used only when the LLM is unavailable.

    This is intentionally NOT a keyword-based fake AI router.
    It simply tells the user that the AI service needs to be
    configured.
    """

    return WorkBuddyResponse(
        agent="🤖 WorkBuddy",
        intent="llm_unavailable",
        response=(
            "I'm ready to help, but my AI service is not "
            "configured yet. Please add your Gemini API key "
            "to the project's `.env` file and restart WorkBuddy."
        ),
        actions=[
            "Configure the LLM API",
            "Try your question again",
        ],
        knowledge_used=[],
    )


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def handle_user_message(
    message: str,
    ctx: ConversationContext,
) -> Tuple[str, ConversationContext, Dict[str, Any]]:

    """
    Main interface used by app.py.

    Returns:

        reply
        updated conversation context
        metadata
    """

    message = message.strip()

    if not message:

        result = WorkBuddyResponse(
            agent="🤖 WorkBuddy",
            intent="empty_message",
            response=(
                "I'm here! Tell me what you need help with — "
                "HR, IT, onboarding, workplace policies, "
                "or even drafting an email."
            ),
            actions=[
                "Ask about an HR policy",
                "Ask for workplace assistance",
            ],
        )

    else:

        try:

            result = generate_llm_response(
                message,
                ctx,
            )

        except Exception as exc:

            print(
                "WorkBuddy LLM error:",
                repr(exc)
            )

            log_workflow(
                agent="WorkBuddy",
                skill="GenerateWorkplaceResponse",
                status="Failed",
                details=str(exc),
            )

            result = fallback_response(
                message
            )


    # --------------------------------------------------------
    # UPDATE CONVERSATION CONTEXT
    # --------------------------------------------------------

    ctx.last_intent = result.intent


    ctx.history.append(
        {
            "role": "user",
            "content": message,
        }
    )


    ctx.history.append(
        {
            "role": "assistant",
            "content": result.response,
        }
    )


    # Keep the context reasonably small.
    if len(ctx.history) > 20:

        ctx.history = ctx.history[-20:]


    # --------------------------------------------------------
    # STORE LAST RESPONSE METADATA
    # --------------------------------------------------------

    ctx.metadata = {
        "agent": result.agent,
        "intent": result.intent,
        "actions": result.actions,
        "knowledge_used": result.knowledge_used,
        "timestamp": datetime.datetime.now().isoformat(),
    }


    # --------------------------------------------------------
    # METADATA SENT BACK TO APP.PY
    # --------------------------------------------------------

    metadata = {
        "agent": result.agent,
        "intent": result.intent,
        "actions": result.actions,
        "knowledge_used": result.knowledge_used,
    }


    return (
        result.response,
        ctx,
        metadata,
    )
