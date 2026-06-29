from ollama import chat


def ask_qwen(prompt: str) -> str:
    response = chat(
        model="qwen2.5:7b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]


if __name__ == "__main__":
    answer = ask_qwen(
        "You are a basketball coach. In one sentence, explain why rebounding wins games."
    )

    print(answer)