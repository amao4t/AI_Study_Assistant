import traceback
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

# Load summarization model from HuggingFace
try:
    summarizer = pipeline('summarization', model='facebook/bart-large-cnn')
except Exception as e:
    print(f"Error loading summarization model: {e}")
    print(traceback.format_exc())
    summarizer = None

# Load the T5-small model with the appropriate tokenizer for question generation
model_name = "t5-small"
try:
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    question_generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer)
except Exception as e:
    print(f"Error loading question generation model: {e}")
    print(traceback.format_exc())
    question_generator = None

def split_content(content, max_length=1000):
    """Split content into smaller chunks to avoid exceeding model token limit."""
    return [content[i:i+max_length] for i in range(0, len(content), max_length)]

def summarize_content(content):
    """Summarize the provided content using the summarizer model.
    
    Args:
        content (str): The text content to be summarized.

    Returns:
        tuple: A tuple containing the summary text or None and an error message or None.
    """
    if not summarizer:
        return None, "Summarizer model is not available."

    # Use a detailed setting for all summaries
    max_len = 300
    min_len = 100

    try:
        # If content is too long, split it into smaller chunks
        if len(content) > 1000:
            chunks = split_content(content)
            summaries = []
            for chunk in chunks:
                summary = summarizer(chunk, max_length=max_len, min_length=min_len, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            return " ".join(summaries), None
        else:
            summary = summarizer(content, max_length=max_len, min_length=min_len, do_sample=False)
            return summary[0]['summary_text'], None
    except Exception as e:
        return None, str(e)

def generate_quiz_questions(summary):
    """Generate quiz questions based on the provided summary.

    Args:
        summary (str): The summary text to generate questions from.

    Returns:
        tuple: A tuple containing the generated questions or None and an error message or None.
    """
    if not question_generator:
        return None, "Question generation model is not available."

    input_text = "Generate multiple-choice questions based on the following summary: " + summary
    try:
        questions = question_generator(input_text, max_length=256, do_sample=False)
        return questions[0]['generated_text'], None
    except Exception as e:
        return None, f"Error generating questions: {str(e)}"
