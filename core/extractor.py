#ActionableItems, decision, questions

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_llm():
    return ChatMistralAI(model = "mistral-small-latest",
                         mistral_api_key = os.getenv("MISTRAL_API_KEY"))


def split_transcripts(transcript : str) -> list:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap = 200
    )
    return splitter.split_text(transcript)


def build_chain(system_prompt : str):
    llm = get_llm()
    return RunnablePassthrough() | RunnablePassthrough(lambda x : {"text" : x}) | ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}")
    ]) | llm |StrOutputParser()


def extract_action_items(transcript : str) -> str:
    chunks = split_transcripts(transcript)

    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )
    chunk_summaries = [chain.invoke(chunk) for chunk in chunks]
    combined = "\n\n".join(chunk_summaries)
    consolidation_chain = build_chain(
        "You are given action items extracted from different parts of a meeting transcript. "
        "Merge and deduplicate them into a single clean numbered list. "
        "Keep Task, Owner, and Deadline for each."
    )

    return consolidation_chain.invoke(combined)


def extract_key_decisions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"
    )
    return chain.invoke(transcript)


def extract_questions(transcript: str) -> str:
    chain = build_chain(
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"
    )
    return chain.invoke(transcript)

