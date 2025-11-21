# backend.py — Enhanced Version (Option B)

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List
import uuid
import datetime

# --------------------------------------------------------------------
# MOCK DATABASES
# --------------------------------------------------------------------
LEAVE_BALANCES = {
    "akshaya": 4,
    "default": 6,
}

IT_TICKETS: List[Dict] = []
ONBOARDING_CASES: List[Dict] = []
WORKFLOW_LOGS: List[Dict] = []   # NEW – global workflow execution log


# --------------------------------------------------------------------
# CONTEXT OBJECT
# --------------------------------------------------------------------
@dataclass
class ConversationContext:
    user_id: str = "akshaya"
    last_intent: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------
def detect_intent(message: str) -> str:
    text = message.lower()

    if "leave" in text or "holiday" in text or "vacation" in text:
        return "check_leave"

    if any(w in text for w in ["access", "salesforce", "jira", "vpn", "github", "tool"]):
        return "request_access"

    if "onboard" in text or "joining" in text or "new hire" in text or "new analyst" in text:
        return "start_onboarding"

    if "policy" in text or "hr policy" in text or "handbook" in text:
        return "hr_policy"

    return "general"


def make_id(prefix: str) -> str:
    return prefix + "-" + uuid.uuid4().hex[:6].upper()


def log_workflow(agent: str, skill: str, status: str, ref_id: str | None = None, details: str | None = None):
    """Append a workflow execution log entry."""
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


# --------------------------------------------------------------------
# SKILLS (WITH LOGGING & SIMULATED STEPS)
# --------------------------------------------------------------------
def skill_check_leave_balance(user_id: str):
    balance = LEAVE_BALANCES.get(user_id, LEAVE_BALANCES["default"])
    text = (
        f"🟣 **HR Agent**\n\n"
        f"You currently have **{balance} days** of casual leave remaining.\n"
        f"If you want, I can help you plan a leave request next."
    )
    meta = {
        "agent": "HR",
        "type": "leave_check",
        "balance": balance,
        "timestamp": datetime.datetime.now().isoformat()
    }

    log_workflow(
        agent="HR Agent",
        skill="CheckLeaveBalance",
        status="Completed",
        ref_id=user_id,
        details=f"Leave balance: {balance} days",
    )

    return text, meta


def skill_request_tool_access(user_id: str, tool_name: str):
    # Step 1 – create ticket in IT system
    ticket_id = make_id("TKT")
    ticket = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "tool": tool_name,
        "status": "Pending Manager Approval",
        "created_at": datetime.datetime.now().isoformat(),
    }
    IT_TICKETS.append(ticket)

    log_workflow(
        agent="IT Agent",
        skill="CreateAccessRequest",
        status="Created",
        ref_id=ticket_id,
        details=f"Tool: {tool_name}",
    )

    # Step 2 – simulate manager approval (for demo, auto-approve)
    ticket["status"] = "Approved"
    log_workflow(
        agent="Manager Agent",
        skill="ApproveAccessRequest",
        status="Approved",
        ref_id=ticket_id,
        details=f"Auto-approved for demo for {tool_name}",
    )

    # Step 3 – simulate access granted
    log_workflow(
        agent="IT Agent",
        skill="GrantAccess",
        status="Completed",
        ref_id=ticket_id,
        details=f"Access granted to {tool_name}",
    )

    text = (
        f"🔵 **IT Agent**\n\n"
        f"Your access request for **{tool_name}** has been processed.\n\n"
        f"**Ticket:** `{ticket_id}`\n"
        f"**Status:** ✅ Approved\n"
        f"**Action:** Access has been granted.\n\n"
        f"*For the purposes of this demo, manager approval is automatically simulated.*"
    )

    return text, ticket


def skill_start_onboarding(user_id: str, role: str):
    case_id = make_id("OB")
    steps = [
        "HR profile created",
        "Laptop & VPN request raised",
        "Tool access checklist prepared",
        "Intro meeting with manager scheduled"
    ]

    case = {
        "case_id": case_id,
        "user_id": user_id,
        "role": role,
        "steps": steps,
        "status": "Completed",   # For demo we mark full workflow done instantly
        "started_at": datetime.datetime.now().isoformat(),
    }
    ONBOARDING_CASES.append(case)

    # log each step as if orchestrated
    log_workflow(
        agent="Onboarding Agent",
        skill="StartOnboarding",
        status="Initiated",
        ref_id=case_id,
        details=f"Role: {role}",
    )
    for s in steps:
        log_workflow(
            agent="Onboarding Agent",
            skill="OnboardingStep",
            status="Completed",
            ref_id=case_id,
            details=s,
        )

    text = (
        f"🟢 **Onboarding Agent**\n\n"
        f"Started onboarding workflow for **{role}**.\n\n"
        f"**Case ID:** `{case_id}`\n"
        f"**Status:** ✅ Completed (all steps initiated in this demo)\n\n"
        f"**Steps executed:**\n" +
        "\n".join([f"- {s}" for s in steps])
    )

    return text, case


def skill_get_hr_policy(topic: str = "leave"):
    text = (
        f"🟣 **HR Agent**\n\n"
        f"Here’s a quick summary of the **{topic} policy**:\n"
        "- Leave must be applied 2 days in advance.\n"
        "- Emergency leave can be approved by the reporting manager.\n"
        "- Paid leave resets annually.\n\n"
        "For complete details, please visit the HR handbook or HR portal."
    )
    meta = {
        "agent": "HR",
        "type": "policy",
        "topic": topic,
        "timestamp": datetime.datetime.now().isoformat()
    }

    log_workflow(
        agent="HR Agent",
        skill="SummarizePolicy",
        status="Completed",
        ref_id=topic,
        details="Policy summary provided to user",
    )

    return text, meta


# --------------------------------------------------------------------
# MAIN ROUTER — SIMULATING WATSONX ORCHESTRATE CHOOSING SKILLS
# --------------------------------------------------------------------
def handle_user_message(message: str, ctx: ConversationContext) -> Tuple[str, ConversationContext]:
    intent = detect_intent(message)
    ctx.last_intent = intent

    if intent == "check_leave":
        reply, meta = skill_check_leave_balance(ctx.user_id)

    elif intent == "request_access":
        lower = message.lower()
        tool = "Requested Tool"
        for t in ["salesforce", "jira", "vpn", "github", "email"]:
            if t in lower:
                tool = t.capitalize()
                break
        reply, meta = skill_request_tool_access(ctx.user_id, tool)

    elif intent == "start_onboarding":
        lower = message.lower()
        role = "New Hire"
        for r in ["analyst", "developer", "engineer", "manager", "intern"]:
            if r in lower:
                role = r.title()
                break
        reply, meta = skill_start_onboarding(ctx.user_id, role)

    elif intent == "hr_policy":
        reply, meta = skill_get_hr_policy()

    else:
        reply = (
            "🤖 **General Assistant**\n\n"
            "I can help you with:\n"
            "- Checking your leave balance\n"
            "- Requesting access (Salesforce, Jira, VPN…)\n"
            "- Starting onboarding workflows\n"
            "- Summarizing HR policies\n\n"
            "Try asking me something like:\n"
            "- *\"How many casual leaves do I have?\"*\n"
            "- *\"I need Salesforce access\"*\n"
            "- *\"Start onboarding a new analyst\"*"
        )
        meta = {"agent": "General", "type": "info"}

        log_workflow(
            agent="General Assistant",
            skill="HelpMessage",
            status="Shown",
            ref_id=None,
            details="Displayed help options to user",
        )

    return reply, ctx
