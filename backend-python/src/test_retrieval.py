from vector_store import (
    get_chroma_client,
    get_or_create_collection,
    query_collection
)

client = get_chroma_client()

collection = get_or_create_collection(client)

results = query_collection(
    collection,
    "How many annual leave days do employees receive?",
    n_results=3
)

for result in results:
    print("\n")
    print("=" * 80)
    print(result["metadata"])
    print(result["document"][:500])