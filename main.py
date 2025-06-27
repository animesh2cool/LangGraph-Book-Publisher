import asyncio
from langgraph_workflow.graph import build_workflow
from agents.versioning_agent import VersioningAgent

async def run_workflow():
    workflow = build_workflow()

    initial_state = {
        "raw_text": None,
        "rewritten_text": None,
        "reviewed_text": None,
        "final_text": None,
        "retrieval_results": None,
        "screenshot_path": None
    }

    final_state = await workflow.ainvoke(initial_state)

    print("\n--- FINAL REVIEWED TEXT ---\n")
    print(final_state["reviewed_text"])

    version_agent = VersioningAgent()
    records = version_agent.get_versions("chapter1")
    print("\n[DEBUG] Stored Versions:\n")
    for doc, meta in zip(records["documents"], records["metadatas"]):
        print(f"- {meta['version_type']} by {meta['author']} @ {meta['timestamp']}\n{doc[:300]}...\n{'-'*60}")

    print("\n--- FINAL TEXT APPROVED BY HUMAN ---\n")
    print(final_state["final_text"])

    print("\n--- SIMILAR PREVIOUS VERSIONS ---\n")
    retrievals = final_state.get("retrieval_results", {})
    if retrievals:
        for i, (text, meta) in enumerate(zip(retrievals["matched_versions"], retrievals["metadata"])):
            print(f"Match {i+1}: [{meta['version_type']}] by {meta['author']} at {meta['timestamp']}")
            print(text)
            print("-" * 60)
    else:
        print("No similar versions found.")


if __name__ == "__main__":
    asyncio.run(run_workflow())