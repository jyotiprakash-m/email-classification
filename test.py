import ollama

response = ollama.generate(
    model="jharkhand-sql",
    prompt="Show all details of the application with application number APP-2025-005"
)

print(response['response'])
