from ddgs import DDGS


def search(query, max_results=5):
    with DDGS() as ddgs:
        results = list(
            ddgs.text(
                query,
                max_results=max_results
            )
        )

    return results


if __name__ == "__main__":

    query = input("Search> ")

    results = search(query)

    print("\n===== RESULTS =====\n")

    for i, r in enumerate(results, start=1):

        print(f"[{i}]")

        print("TITLE:")
        print(r.get("title", ""))

        print("\nBODY:")
        print(r.get("body", ""))

        print("\nURL:")
        print(r.get("href", ""))

        print("\n" + "=" * 60 + "\n")