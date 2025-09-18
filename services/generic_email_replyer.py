from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from core import settings

# Initialize the model
llm = init_chat_model(
    model="gpt-4o-mini",
    temperature=0,  
    api_key=settings.OPENAI_API_KEY
)

# System prompt to guide the reply style
system_prompt = """
You are an assistant that generates polite, professional, and context-aware email replies. 
Rules:
1. Reply in a formal and concise tone.
2. Acknowledge the sender’s request or concern.
3. Provide a generic but relevant response (no sensitive or fabricated details).
4. End with a professional closing.
"""

# Function to generate reply
def generate_email_reply(email_text: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"Email received:\n\n{email_text}\n\nWrite a professional reply:")
    ])
    
    chain = prompt | llm
    response = chain.invoke({})
    # Ensure the return value is always a string
    if isinstance(response.content, str):
        return response.content
    else:
        return str(response.content)

# Example usage
email = """
Hello, 
I am following up regarding the invoice I sent earlier this month. 
Could you please confirm if it has been processed? 
Thank you for your assistance. 
Best regards, 
Priya
"""

# print(generate_email_reply(email))

