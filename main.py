import os
from openai import OpenAI
import streamlit as st
import time
from streamlit_extras.buy_me_a_coffee import button as buy_me_a_coffee_button

env_vars = {}
if os.getenv("ENV_NAME") == "local":
    from dotenv import find_dotenv, load_dotenv, dotenv_values

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    env_vars = dotenv_values(dotenv_path)

buy_me_a_coffee_button(username="stonebat", floating=True, width=221)

# OpenAI Key 입력 받기
openai_api_key = st.text_input("OPENAI_API_KEY", type="password")

# Check if openai_api_key is empty and get it from the environment variable if necessary
if not openai_api_key:
    openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

    # Initialize session state for file_id and assistant_id
    if "file_id" not in st.session_state:
        st.session_state.file_id = None

    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = None

    # Upload file if not already uploaded
    if st.session_state.file_id is None:
        file_id = "file-lyu8Rj0cwTovz8meUB7Lirin"
        try:
            existing_files = client.files.list()
            if not any(f.id == file_id for f in existing_files.data):
                file_id = client.files.create(
                    file=open("unsu.pdf", "rb"), purpose="assistants"
                ).id
                st.session_state.file_id = file_id
            else:
                st.session_state.file_id = file_id
        except Exception as e:
            print(f"An error occurred: {e}")

    # Create or get assistant if not already done
    if st.session_state.assistant_id is None:
        existing_assistants = client.beta.assistants.list()
        assistant = next(
            (a for a in existing_assistants.data if a.name == "현진건 작가님 2"), None
        )

        if assistant:
            st.session_state.assistant_id = assistant.id
        else:
            st.session_state.assistant_id = client.beta.assistants.create(
                instructions='당신은 소설 "운수 좋은 날" 집필한 현진건 작가님 입니다.',
                name="현진건 작가님 by Coding",
                tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
                model="gpt-4o-mini",
                file_ids=[st.session_state.file_id],
            ).id

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    thread_id = st.session_state.thread_id

    thread_messages = client.beta.threads.messages.list(thread_id, order="asc")

    st.header("현진건 작가님과의 대화")

    for msg in thread_messages.data:
        with st.chat_message(msg.role):
            st.write(msg.content[0].text.value)

    prompt = st.chat_input("물어보고 싶은 것을 입력하세요!")
    if prompt:
        message = client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=prompt
        )
        with st.chat_message(message.role):
            st.write(message.content[0].text.value)

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=st.session_state.assistant_id,
        )

        with st.spinner("응답 기다리는 중..."):
            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        with st.chat_message(messages.data[0].role):
            st.write(messages.data[0].content[0].text.value)
