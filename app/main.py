import time
from dataclasses import dataclass

import streamlit as st
from langchain.agents import AgentExecutor

from app.agent.executor import init_agent_executor
from app.agent.tools import (
    AddEmployeeToHRTool,
    CancelTimeOffRequestTool,
    CreateCalendarEventTool,
    EstimateTimeOffBalanceTool,
    HRPolicyEmailTool,
    HRPolicyQATool,
    MakeTimeOffRequestTool,
    ModifyEmployeeTool,
    RespondTool,
    SlackInviteTool,
    ViewTimeOffRequestsTool,
    WelcomeEmailTool,
)
from app.utils import CaptureStdout, no_ansi_string


@dataclass
class RoleType:
    USER = "user"
    ASSISTANT = "assistant"


class MariaApp:
    def __init__(self) -> None:
        if "messages" not in st.session_state:
            self.init_session_state()

    def init_session_state(self) -> None:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": """
                Hi, I am Maria, your personal HR assistant. To get started, can you please provide the following information:\n
                    - First Name
                    - Last Name
                    - Email Address
                I will then:\n
                    1. Send you a welcome email, the HR policies and a Slack invite.
                    2. Schedule a calendar event for your onboarding.
                    3. Enroll you in the HR system.
                Thanks!
                """,
                "log": [],
            }
        ]
        st.session_state.debug_logs = []
        st.session_state.thinking = False

        # Onboarding status
        st.session_state.welcome_email_sent = False
        st.session_state.policies_email_sent = False
        st.session_state.slack_invite_sent = False
        st.session_state.calendar_event_created = False
        st.session_state.enrolled_in_HR_system = False

    def onboarding_status_widget(self) -> None:
        with st.expander("Onboarding Status", expanded=True):
            st.checkbox(
                "Welcome Email",
                value=st.session_state.welcome_email_sent,
                disabled=True,
            )

            st.checkbox(
                "Send HR Policies",
                value=st.session_state.policies_email_sent,
                disabled=True,
            )

            st.checkbox(
                "Slack Invite",
                value=st.session_state.slack_invite_sent,
                disabled=True,
            )

            st.checkbox(
                "Schedule Onboarding Event",
                value=st.session_state.calendar_event_created,
                disabled=True,
            )

            st.checkbox(
                "Enroll in HR System",
                value=st.session_state.enrolled_in_HR_system,
                disabled=True,
            )

    def sidebar(self) -> None:
        with st.sidebar:
            st.title("Maria, your personal HR assistant")
            # Description
            st.markdown(
                """
                This is Maria, your personal HR assistant.
                She can help you with the following tasks:
                - Send a welcome email.
                - Send a copy of the HR policies via email.
                - Invite to the company Slack via email.
                - Schedule calendar events.
                - Answer questions about the company's HR policies.
                - Make and edit time off requests.
                - Estimate your remaining time off balance.
                """
            )

            st.markdown("<br>", unsafe_allow_html=True)

            self.onboarding_status_widget()

            #  Add a debug mode to show the logs
            with st.expander("Debug mode"):
                st.warning(
                    "Toggling debug mode while the agent is thinking will cause issues."
                )
                debug = st.checkbox("Debug mode", disabled=st.session_state.thinking)
                st.session_state.debug = debug

            if st.button("Reset", use_container_width=True):
                self.init_session_state()

    def render_chat(self) -> None:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["log"] and st.session_state.debug:
                    st.write(message["log"])

    def store_message(self, role: str, content: str, log: list[str] = []) -> None:
        st.session_state.messages.append({"role": role, "content": content, "log": log})

    def init_agent(self) -> AgentExecutor:
        # Status callbacks
        def set_welcome_email_status() -> None:
            st.session_state.welcome_email_sent = True

        def set_policies_email_status() -> None:
            st.session_state.policies_email_sent = True

        def set_slack_invite_status() -> None:
            st.session_state.slack_invite_sent = True

        def set_calendar_event_status() -> None:
            st.session_state.calendar_event_created = True

        def set_enrolled_in_HR_system_status() -> None:
            st.session_state.enrolled_in_HR_system = True

        tools = [
            RespondTool(),
            WelcomeEmailTool(callback=set_welcome_email_status),
            HRPolicyEmailTool(callback=set_policies_email_status),
            SlackInviteTool(callback=set_slack_invite_status),
            CreateCalendarEventTool(callback=set_calendar_event_status),
            AddEmployeeToHRTool(callback=set_enrolled_in_HR_system_status),
            HRPolicyQATool(),
            ModifyEmployeeTool(),
            ViewTimeOffRequestsTool(),
            MakeTimeOffRequestTool(),
            CancelTimeOffRequestTool(),
            EstimateTimeOffBalanceTool(),
        ]
        return init_agent_executor(tools, verbose=True)

    def handle_chat_input(self) -> None:
        if user_input := st.chat_input("What's up?"):
            # Count the number of words in the user input
            num_words = len(user_input.split())
            if num_words > 500:
                st.error("Please keep your message under 500 words.")
                return

            self.store_message(RoleType.USER, user_input)

            with st.chat_message(RoleType.USER):
                st.markdown(user_input)

            agent_executor = self.init_agent()

            with st.chat_message(RoleType.ASSISTANT):
                message_placeholder = st.empty()
                full_response = ""

                with st.spinner("Thinking..."):
                    # TODO - manage conversation history length
                    with CaptureStdout() as c:
                        llm_output = agent_executor.invoke(
                            {
                                "input": user_input,
                                "chat_history": st.session_state.messages[:-1],
                            }
                        )["output"]

                for response in llm_output:
                    full_response += response
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.02)

                logs = no_ansi_string(c.getvalue()).split("\n")
                logs = list(filter(None, logs))  # Remove blank lines
                if st.session_state.debug:
                    st.write(logs)

                message_placeholder.markdown(full_response)
            self.store_message(RoleType.ASSISTANT, full_response, logs)

    def run(self) -> None:
        st.header("Talk to me!")

        self.sidebar()
        self.render_chat()
        self.handle_chat_input()


if __name__ == "__main__":
    MariaApp().run()
