from transformers import T5Tokenizer, T5ForConditionalGeneration

tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5ForConditionalGeneration.from_pretrained("t5-small")

def generate_response(query, intent):

    if intent == "greeting":
        return "Hello! How can I assist you today?"

    elif intent == "refund":
        return "We’re sorry for your experience. Your refund request has been noted and will be processed shortly."

    elif intent == "complaint":
        return "We sincerely apologize. Please share more details so we can resolve this issue."

    elif intent == "technical":
        return "Please try restarting the app or check your internet connection."

    elif intent == "inquiry":
        return "Thanks for reaching out! We will provide the required information shortly."

    # fallback (optional AI generation)
    prompt = f"answer politely: {query}"

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=80)

    return tokenizer.decode(outputs[0], skip_special_tokens=True)