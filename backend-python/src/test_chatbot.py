import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

from src.chatbot import chatbot

while True:
    question = input("\nAsk Question: ")

    if question.lower() == "exit":
        break

    response = chatbot.ask(question)

    print("\n")
    print("=" * 80)
    print("\nANSWER:\n")
    print(response["answer"])

    print("\nSOURCES:\n")
    for source in response["sources"]:
        print(f"{source['section']} -> {source['heading']}")

    if "timing" in response:
        timing = response["timing"]
        print("\nTIMING:\n")
        if timing.get("cache_hit"):
            print("  Cache Hit: Yes")
            print(f"  Total Time: {timing['total_time']:.3f}s")
        else:
            print(f"  Retrieval Time: {timing.get('retrieval_time', 0):.2f}s")
            print(f"  Prompt Build Time: {timing.get('prompt_build_time', 0):.2f}s")
            print(f"  Gemini Time: {timing.get('gemini_time', 0):.2f}s")
            print(f"  Total Time: {timing.get('total_time', 0):.2f}s")