from bot import openai_client


async def get_chat_completion(prompt: str, system: str= None, model="gpt-3.5-turbo", temperature=0.5, max_tokens=500)-> str :

    messages = []

    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None


