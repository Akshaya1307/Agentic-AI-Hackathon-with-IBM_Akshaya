# app.py — WorkBuddy LLM-Powered Employee Copilot

import streamlit as st
import datetime

from backend import (
    handle_user_message,
    ConversationContext,
    WORKFLOW_LOGS,
)


# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="WorkBuddy – HR & IT Copilot",
    page_icon="🤖",
    layout="wide",
)


# ------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "ctx" not in st.session_state:
    st.session_state.ctx = ConversationContext()

if "activity" not in st.session_state:
    st.session_state.activity = []


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

with st.sidebar:

    st.markdown("## 🤖 WorkBuddy Copilot")
    st.markdown("### *Unified Employee Assistance*")

    st.markdown("##### 👑 Logged in as:")
    st.success("**Naga Akshaya Boyidi**")

    st.markdown("---")

    st.markdown("### 🧠 AI Capabilities")

    st.markdown(
        """
        - 🟣 HR & Policy Assistance
        - 🔵 IT Support Guidance
        - 🟢 Onboarding Assistance
        - 📝 Email & Letter Drafting
        - 📚 Workplace Information
        - 💬 Conversational Help
        """
    )

    st.markdown("---")

    st.markdown("### 🔧 Powered Conceptually By")

    st.markdown("- **IBM watsonx Orchestrate**")
    st.markdown("- **IBM watsonx.ai**")
    st.markdown("- **IBM Cloudant**")

    st.markdown("---")

    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------

    st.markdown("### ⚡ Try WorkBuddy")

    st.caption(
        "These are natural conversation starters. "
        "You can also ask anything in your own words."
    )

    if st.button(
        "📅 I need help with leave",
        use_container_width=True,
    ):
        st.session_state.pending_prompt = (
            "I have a personal event coming up and may need leave. "
            "Can you tell me what I should do?"
        )

    if st.button(
        "📜 Explain an HR policy",
        use_container_width=True,
    ):
        st.session_state.pending_prompt = (
            "Can you explain the relevant HR policies I should know as an employee?"
        )

    if st.button(
        "📧 Help me write an email",
        use_container_width=True,
    ):
        st.session_state.pending_prompt = (
            "I need help formatting a professional email to my manager."
        )

    if st.button(
        "💻 I need IT help",
        use_container_width=True,
    ):
        st.session_state.pending_prompt = (
            "I'm having an IT-related problem. Can you help me figure out what to do?"
        )

    if st.button(
        "🟢 Help with onboarding",
        use_container_width=True,
    ):
        st.session_state.pending_prompt = (
            "I'm joining a new team soon. What should I prepare for onboarding?"
        )

    st.markdown("---")

    st.info(
        "💡 You don't need to use specific commands. "
        "Just describe your situation naturally."
    )


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🤖 WorkBuddy – Unified HR & IT Copilot")

st.caption(
    "AI-powered employee assistance for HR, IT & onboarding — "
    "conceptually powered by IBM watsonx Orchestrate."
)


# ------------------------------------------------------------
# TABS
# ------------------------------------------------------------

tabs = st.tabs(
    [
        "💬 Chat",
        "📊 Dashboard",
    ]
)


# ============================================================
# TAB 1 — CHAT
# ============================================================

with tabs[0]:

    st.markdown("### 💬 Chat with WorkBuddy")

    st.caption(
        "Ask questions naturally. WorkBuddy can explain policies, "
        "guide you through workplace tasks, and help create professional messages."
    )

    # --------------------------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.messages:

        role = message["role"]
        content = message["content"]

        if role == "user":

            with st.chat_message("user"):
                st.markdown(
                    f"**👤 You**\n\n{content}"
                )

        else:

            with st.chat_message("assistant"):

                agent = message.get("agent")

                if agent:
                    st.markdown(
                        f"**{agent}**"
                    )

                st.markdown(
                    content,
                    unsafe_allow_html=True,
                )


    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    user_input = st.chat_input(
        "Tell WorkBuddy what you need help with..."
    )


    # --------------------------------------------------------
    # HANDLE QUICK ACTION
    # --------------------------------------------------------

    if "pending_prompt" in st.session_state:

        user_input = st.session_state.pending_prompt

        del st.session_state.pending_prompt


    # --------------------------------------------------------
    # PROCESS USER MESSAGE
    # --------------------------------------------------------

    if user_input:

        # ----------------------------------------------------
        # STORE USER MESSAGE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        with st.chat_message("user"):

            st.markdown(
                f"**👤 You**\n\n{user_input}"
            )


        # ----------------------------------------------------
        # CALL BACKEND / LLM
        # ----------------------------------------------------

        try:

            result = handle_user_message(
                user_input,
                st.session_state.ctx,
            )


            # ------------------------------------------------
            # SUPPORT NEW BACKEND RESPONSE
            #
            # Expected:
            #
            # reply, ctx, metadata
            #
            # ------------------------------------------------

            if len(result) == 3:

                reply, ctx, metadata = result

            else:

                # Temporary compatibility with old backend
                reply, ctx = result

                metadata = {
                    "agent": "🤖 WorkBuddy",
                    "intent": None,
                    "actions": [],
                }


            st.session_state.ctx = ctx


            # ------------------------------------------------
            # EXTRACT RESPONSE INFORMATION
            # ------------------------------------------------

            agent = metadata.get(
                "agent",
                "🤖 WorkBuddy",
            )

            intent = metadata.get(
                "intent"
            )

            actions = metadata.get(
                "actions",
                [],
            )


            # ------------------------------------------------
            # DISPLAY ASSISTANT RESPONSE
            # ------------------------------------------------

            with st.chat_message("assistant"):

                st.markdown(
                    f"**{agent}**"
                )

                st.markdown(
                    reply,
                    unsafe_allow_html=True,
                )


            # ------------------------------------------------
            # STORE ASSISTANT RESPONSE
            # ------------------------------------------------

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": reply,
                    "agent": agent,
                    "intent": intent,
                }
            )


            # ------------------------------------------------
            # STORE ACTIVITY
            # ------------------------------------------------

            st.session_state.activity.append(
                {
                    "time": datetime.datetime.now().strftime(
                        "%H:%M:%S"
                    ),
                    "agent": agent,
                    "intent": intent or "general",
                    "message": user_input,
                    "actions": actions,
                }
            )


        except Exception as e:

            # ------------------------------------------------
            # FRIENDLY ERROR HANDLING
            # ------------------------------------------------

            error_message = (
                "⚠️ **I'm having trouble processing that right now.**\n\n"
                "Please try again in a moment."
            )

            with st.chat_message("assistant"):

                st.markdown(
                    "**🤖 WorkBuddy**"
                )

                st.markdown(
                    error_message
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "agent": "🤖 WorkBuddy",
                }
            )

            # Keep actual error out of the user-facing UI
            # but print it for local debugging.
            print(
                "WorkBuddy backend error:",
                repr(e)
            )


# ============================================================
# TAB 2 — DASHBOARD
# ============================================================

with tabs[1]:

    st.markdown(
        "## 📊 WorkBuddy Activity Dashboard"
    )

    st.caption(
        "Overview of recent conversations and agent/workflow activity."
    )


    # --------------------------------------------------------
    # SUMMARY CARDS
    # --------------------------------------------------------

    total_conversations = len(
        st.session_state.activity
    )

    total_workflows = len(
        WORKFLOW_LOGS
    )

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "💬 Conversations",
            total_conversations,
        )


    with col2:

        st.metric(
            "⚙️ Workflow Events",
            total_workflows,
        )


    with col3:

        if st.session_state.activity:

            latest_agent = st.session_state.activity[-1]["agent"]

        else:

            latest_agent = "—"

        st.metric(
            "🤖 Latest Agent",
            latest_agent,
        )


    st.markdown("---")


    # --------------------------------------------------------
    # RECENT CONVERSATIONS
    # --------------------------------------------------------

    st.markdown(
        "### 💬 Recent WorkBuddy Activity"
    )

    if st.session_state.activity:

        for activity in reversed(
            st.session_state.activity[-10:]
        ):

            with st.container():

                st.markdown(
                    f"""
**[{activity['time']}]** {activity['agent']}

**User:** {activity['message']}

**Intent:** `{activity['intent']}`
"""
                )

                if activity.get("actions"):

                    st.markdown(
                        "**Actions / Assistance:**"
                    )

                    for action in activity["actions"]:

                        st.markdown(
                            f"- {action}"
                        )

                st.markdown("---")

    else:

        st.info(
            "No conversations yet. "
            "Start chatting with WorkBuddy to see activity here."
        )


    # --------------------------------------------------------
    # WORKFLOW LOGS
    # --------------------------------------------------------

    st.markdown(
        "### 📜 Workflow & Agent Execution Logs"
    )

    st.caption(
        "These entries represent the skills/actions executed "
        "by WorkBuddy and can be used to visualize orchestration."
    )


    if WORKFLOW_LOGS:

        for log in reversed(
            WORKFLOW_LOGS[-15:]
        ):

            ref_id = log.get(
                "ref_id"
            ) or "-"

            details = log.get(
                "details"
            ) or "-"

            st.markdown(
                f"""
**[{log.get('time', '-')} ]** `{log.get('agent', 'WorkBuddy')}`

• **Skill:** `{log.get('skill', '-')}`  
• **Status:** **{log.get('status', '-')}**  
• **Ref:** `{ref_id}`  
• **Details:** {details}
"""
            )

            st.markdown("---")

    else:

        st.info(
            "No workflow events yet."
        )


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

st.markdown("---")

st.caption(
    "🤖 WorkBuddy — AI-powered employee assistance | "
    "HR • IT • Onboarding"
)
