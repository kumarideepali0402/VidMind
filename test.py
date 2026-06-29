from dotenv import load_dotenv
load_dotenv()


from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions

source = "https://www.youtube.com/watch?v=tplWXd_T7YQ"
language = "hinglish"  # hinglish for sarvam

chunks = process_input(source)


print("\n=== TRANSCRIPT ===\n")
transcript = transcribe_all(chunks, language=language)

title = generate_title(transcript)
summary = summarize(transcript)


print(f"Title{title}");
print(summary)