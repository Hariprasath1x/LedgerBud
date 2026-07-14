"""AI Financial Advisor Workspace — LedgerBud."""

import streamlit as st
from ui.api_client import api_client

st.title("AI Financial Advisor")
st.markdown("Chat with your intelligent advisor. Powered by Groq and LLaMA 3.1.")

# Initialize chat history in session state
if "advisor_messages" not in st.session_state:
    st.session_state.advisor_messages = [
        {"role": "assistant", "content": "Hello! I'm your LedgerBud AI advisor. How can I help you with your finances today?"}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.advisor_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about your budget, spending, or savings..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    
    # Add user message to chat history
    st.session_state.advisor_messages.append({"role": "user", "content": prompt})

    # Prepare context / history
    # Pass the last few messages as history, excluding the very first greeting to save tokens if needed
    history = st.session_state.advisor_messages[1:-1]

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        answer = ""  # initialize so it's always bound even if the except path runs

        try:
            response = api_client.ask_advisor(question=prompt, history=history)
            answer = response.get("answer", "I'm sorry, I couldn't process that.")
            message_placeholder.markdown(answer)

            # Show debug transparency panel
            with st.expander("View AI Context Payload", expanded=False):
                ctx = response.get("context_summary") or response.get("context") or {}
                st.json(ctx)
                st.caption(f"Provider: {response.get('provider', 'unknown')}")

        except Exception as e:
            answer = f"Error communicating with AI Advisor: {e}"
            message_placeholder.error(answer)

        # Append the final assistant message to chat history (always bound)
        if answer:
            st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
