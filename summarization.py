from langchain_google_genai import ChatGoogleGenerativeAI



def summarize_note(content):
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key="your-gemini-api-key")
    response = llm.invoke(f"Summarize this note: {content}")
    return response
# Example usage
summary = summarize_note("Your note content here")
print(summary)
# Output: "A summary of the note content."
# Note: Replace "Your note content here" with the actual content of the note you want to summarize.
