import streamlit as st
import uuid
import sys
from pathlib import Path
import json, os, sys, re, random, traceback

import kendra_chat_anthropic as anthropic

USER_ICON = "images/user-icon.png"
AI_ICON = "images/ai-icon.png"
MAX_HISTORY_LENGTH = 5

PROVIDER_MAP = {
    'anthropic': 'Anthropic'
}

docs = [doc.read_text() for doc in sorted((Path.cwd() / "resources" / "docs").iterdir(), key=lambda x: x.name)]
print(docs[0])

# Check if the user ID is already stored in the session state
if 'user_id' in st.session_state:
    user_id = st.session_state['user_id']

# If the user ID is not yet stored in the session state, generate a random UUID
else:
    user_id = str(uuid.uuid4())
    st.session_state['user_id'] = user_id


st.session_state['llm_app'] = anthropic
st.session_state['llm_chain'] = anthropic.build_chain()

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
    
if "chats" not in st.session_state:
    st.session_state.chats = [
        {
            'id': 0,
            'question': '',
            'answer': ''
        }
    ]

if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = []

if "input" not in st.session_state:
    st.session_state.input = ""


st.markdown("""
        <style>
               .block-container {
                    padding-top: 32px;
                    padding-bottom: 32px;
                    padding-left: 0;
                    padding-right: 0;
                }
                .element-container img {
                    background-color: #000000;
                }

                .main-header {
                    font-size: 24px;
                }
        </style>
        """, unsafe_allow_html=True)

def write_logo():
    col1, col2, col3 = st.columns([5, 1, 5])
    with col2:
        st.image(AI_ICON, use_column_width='always') 

def write_top_bar():
    col1, col2, col3 = st.columns([1,10,2])
    with col1:
        st.image(AI_ICON, use_column_width='always')
    with col2:
        header = f"Medical Terminology Translator powered by Amazon Kendra and Amazon Bedrock (Claude)!"
        st.write(f"<h3 class='main-header'>{header}</h3>", unsafe_allow_html=True)
    with col3:
        clear = st.button("Clear Chat")
    return clear

clear = write_top_bar()

st.markdown('---')
st.write("""\
A patient’s diagnosis and treatment plan may include complex medical terms and concepts 
they’re unfamiliar with. This is especially true for uncommon or complex medical conditions.
A lack of understanding around key treatment issues and how certain terms and concepts are 
communicated through channels such as radiology reports can create problems not only for
 patient outcomes but also for patient-provider relationship.
This tool serves as a utility that helps explain medical terminologies patients are not familiar
with. It can be embedded in patient-facing tools allowing providers to offer a seamless experience
in the way they communicate with the patients in a simplified manner without compromising on the 
accuracy or reporting standards.
""")

if clear:
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.input = ""
    st.session_state["chat_history"] = []

def handle_input():
    input = st.session_state.input
    question_with_id = {
        'question': input,
        'id': len(st.session_state.questions)
    }
    st.session_state.questions.append(question_with_id)

    chat_history = st.session_state["chat_history"]
    if len(chat_history) == MAX_HISTORY_LENGTH:
        chat_history = chat_history[:-1]

    llm_chain = st.session_state['llm_chain']
    chain = st.session_state['llm_app']
    result = chain.run_chain(llm_chain, input, chat_history)
    answer = result['answer']
    chat_history.append((input, answer))
    
    document_list = []
    if 'source_documents' in result:
        for d in result['source_documents']:
            if not (d.metadata['source'] in document_list):
                document_list.append((d.metadata['source']))

    st.session_state.answers.append({
        'answer': result,
        'sources': document_list,
        'id': len(st.session_state.questions)
    })
    st.session_state.input = ""

def write_user_message(md):
    col1, col2 = st.columns([1,12])
    
    with col1:
        st.image(USER_ICON, use_column_width='always')
    with col2:
        st.warning(md['question'])


def render_result(result):
    answer, sources = st.tabs(['Answer', 'Sources'])
    with answer:
        render_answer(result['answer'])
    with sources:
        if 'source_documents' in result:
            render_sources(result['source_documents'])
        else:
            render_sources([])

def render_answer(answer):
    col1, col2 = st.columns([1,12])
    with col1:
        st.image(AI_ICON, use_column_width='always')
    with col2:
        st.info(answer['answer'])

def render_sources(sources):
    col1, col2 = st.columns([1,12])
    with col2:
        with st.expander("Sources"):
            for s in sources:
                st.write(s)

    
docs = [doc.read_text() for doc in sorted((Path.cwd() / "resources" / "docs").iterdir(), key=lambda x: x.name)]

def normalize_ws(doc: str) -> str:
    # keep double-newlines, remove single newlines:
    sentinel = "$%$"
    doc = re.sub(r"\n{2}", sentinel, doc)
    doc = doc.replace("\n", " ")
    doc = doc.replace(sentinel, "\n\n")
    return re.sub(" +", " ", doc)
docs = [normalize_ws(doc.strip()) for doc in docs]


#Each answer will have context of the question asked in order to associate the provided feedback with the respective question
def write_chat_message(md, q):
    chat = st.container()
    with chat:
        render_answer(md['answer'])
        render_sources(md['sources'])

def populate_question(q: str):
    st.session_state.input = q
    handle_input()

        
with st.container():
    for (q, a) in zip(st.session_state.questions, st.session_state.answers):
        write_user_message(q)
        write_chat_message(a, q)

st.markdown('---')
input = st.text_input("You are talking to an AI assistant trained to answer questions about Radiology, Oncology and other medical terminologies, ask any question.", key="input", on_change=handle_input)

cols = st.columns([3]+[1]*len(docs), gap="small")
with cols[0]:
    st.write("Enter a question in the text box above or, you can try a canned document:")
for i, (doc, col) in enumerate(zip(docs, cols[1:])):
    with col:
        def foo(doc=doc):
            populate_question(doc)
        st.button(f"Question #{i}", on_click=foo)

