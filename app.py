# app.py — Pro UI + Uses Workflow Logs

import streamlit as st
from backend import handle_user_message, ConversationContext, WORKFLOW_LOGS
import datetime

st.set_page_config(
    page_title="WorkBuddy – HR & IT Copilot",
    page_icon="🤖",
    layout="wide",
)

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🤖 WorkBuddy Copilot")
    st.markdown("### *Unified HR & IT Automation*")
    
    st.markdown("##### 👑 Logged in as:")
    st.success("**Naga Akshaya Boyidi**")

    st.markdown("---")
    st.markdown("### 🔧 Powered Conceptually By")
    st.markdown("- **IBM watsonx Orchestrate**")
    st.markdown("- **IBM watsonx.ai**")
    st.markdown("- **IBM Cloudant**")
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    if st.button("Check Leave Balance"):
        st.session_state.messages.append(("user", "How many casual leaves do I have?"))

    if st.button("Request Salesforce Access"):
        st.session_state.messages.append(("user", "I need Salesforce access."))

    if st.button("Start Analyst Onboarding"):
        st.session_state.messages.append(("user", "Start onboarding a new analyst"))

    if st.button("Show HR Leave Policy"):
        st.session_state.messages.append(("user", "Show HR leave policy"))

    st.markdown("---")
    st.info("💡 Try your own task in the chat – onboarding, access, HR queries, etc.")


# ------------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "ctx" not in st.session_state:
    st.session_state.ctx = ConversationContext()

if "tickets" not in st.session_state:
    st.session_state.tickets = []

if "onboard_cases" not in st.session_state:
    st.session_state.onboard_cases = []


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("🤖 WorkBuddy – Unified HR & IT Copilot")
st.caption("Agentic AI for HR, IT & Onboarding – conceptually powered by IBM watsonx Orchestrate.")

tabs = st.tabs(["💬 Chat", "📊 Dashboard"])

# ------------------------------------------------------------
# TAB 1 – CHAT
# ------------------------------------------------------------
with tabs[0]:
    st.markdown("### 💬 Chat with WorkBuddy")

    # show history
    for role, content in st.session_state.messages:
        if role == "user":
            with st.chat_message("user"):
                st.markdown(f"**👤 You:**<br>{content}", unsafe_allow_html=True)
        else:
            with st.chat_message("assistant"):
                st.markdown(content, unsafe_allow_html=True)

    # merge quick actions into actual input
    default_prompt = None
    if st.session_state.messages and st.session_state.messages[-1][0] == "user" and \
            st.session_state.messages[-1][1] not in [m[1] for m in st.session_state.messages[:-1]]:
        # last user message was from sidebar button
        default_prompt = st.session_state.messages[-1][1]

    user_input = st.chat_input("Ask WorkBuddy anything about HR, IT, or onboarding...")

    # If user typed via chat_input, that's the latest prompt
    if user_input:
        # USER MSG
        st.session_state.messages.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(f"**👤 You:**<br>{user_input}", unsafe_allow_html=True)

        # BACKEND
        reply, ctx = handle_user_message(user_input, st.session_state.ctx)
        st.session_state.ctx = ctx

        # Which agent is likely responding (for label only)
        lower = user_input.lower()
        if "leave" in lower or "policy" in lower:
            agent = "🟣 HR Agent"
        elif "access" in lower or "salesforce" in lower or "jira" in lower or "vpn" in lower:
            agent = "🔵 IT Agent"
        elif "onboard" in lower or "joining" in lower or "new analyst" in lower:
            agent = "🟢 Onboarding Agent"
        else:
            agent = "🤖 General Assistant"

        with st.chat_message("assistant"):
            st.markdown(f"**{agent} responding…**")
            st.markdown(reply, unsafe_allow_html=True)

        # store in history
        st.session_state.messages.append(("assistant", reply))

        # track basic ticket/onboarding info for dashboard view
        if "Ticket:" in reply:
            st.session_state.tickets.append(
                {
                    "task": user_input,
                    "time": datetime.datetime.now().strftime("%H:%M:%S"),
                    "details": reply,
                }
            )

        if "Started onboarding workflow" in reply or "Started onboarding workflow for" in reply:
            st.session_state.onboard_cases.append(
                {
                    "task": user_input,
                    "time": datetime.datetime.now().strftime("%H:%M:%S"),
                    "details": reply,
                }
            )


# ------------------------------------------------------------
# TAB 2 – DASHBOARD
# ------------------------------------------------------------
with tabs[1]:
    st.markdown("## 📊 WorkBuddy Activity Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🛠️ Recent IT Access Requests")
        if st.session_state.tickets:
            for t in st.session_state.tickets:
                st.info(
                    f"""
**Task:** {t['task']}  
**Time:** {t['time']}  

{t['details']}
                    """
                )
        else:
            st.warning("No IT access requests yet. Ask for Salesforce, Jira, or VPN access from the chat.")

    with col2:
        st.markdown("### 🟢 Onboarding Workflows")
        if st.session_state.onboard_cases:
            for ob in st.session_state.onboard_cases:
                st.success(
                    f"""
**Workflow:** {ob['task']}  
**Started:** {ob['time']}  

{ob['details']}
                    """
                )
        else:
            st.warning("No onboarding workflows started yet. Try: *\"Start onboarding a new analyst\"* in chat.")

    st.markdown("---")
    st.markdown("### 📜 Workflow Execution Logs (simulating watsonx Orchestrate)")

    if WORKFLOW_LOGS:
        for log in reversed(WORKFLOW_LOGS[-15:]):  # show last 15 entries
            st.markdown(
                f"""
**[{log['time']}]** `{log['agent']}`  
• Skill: `{log['skill']}`  
• Status: **{log['status']}**  
• Ref: `{log['ref_id'] or '-'}`
• Details: {log['details'] or '-'}
                """
            )
            st.markdown("---")
    else:
        st.info("No workflow logs yet – interact with WorkBuddy in the chat to generate some.")
