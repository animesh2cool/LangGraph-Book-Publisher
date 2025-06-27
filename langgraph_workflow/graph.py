from langgraph.graph import StateGraph
from typing import TypedDict, Optional

from agents.scraper_agent import ScraperAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent
from agents.human_review_agent import HumanReviewAgent
from agents.versioning_agent import VersioningAgent
from agents.retriever_agent import RetrieverAgent

# State schema
class ChapterState(TypedDict):
    raw_text: Optional[str]
    rewritten_text: Optional[str]
    reviewed_text: Optional[str]
    final_text: Optional[str]
    screenshot_path: Optional[str]
    retrieval_results: Optional[dict]

# Initialize versioning agent
version_agent = VersioningAgent()

# Async node: Scraper
async def scraper_node(state: ChapterState) -> ChapterState:
    agent = ScraperAgent("https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1")
    result = await agent.scrape()

    version_agent.save_version(
        chapter_id="chapter1",
        version_type="raw",
        content=result["text"],
        author="scraper"
    )

    return {
        **state,
        "raw_text": result["text"],
        "screenshot_path": result["screenshot"]
    }

# Sync node: Writer
def writer_node(state: ChapterState) -> ChapterState:
    agent = WriterAgent()
    result = agent.rewrite(state["raw_text"])

    version_agent.save_version(
        chapter_id="chapter1",
        version_type="rewrite",
        content=result["rewritten_text"],
        author="writer"
    )

    return {
        **state,
        "rewritten_text": result["rewritten_text"]
    }

# Sync node: Reviewer
def reviewer_node(state: ChapterState) -> ChapterState:
    agent = ReviewerAgent()
    result = agent.review(state["rewritten_text"])

    version_agent.save_version(
        chapter_id="chapter1",
        version_type="review",
        content=result["reviewed_text"],
        author="reviewer"
    )

    return {
        **state,
        "reviewed_text": result["reviewed_text"]
    }

# Sync node: Human Review
def human_review_node(state: ChapterState) -> ChapterState:
    agent = HumanReviewAgent()
    result = agent.review(state["reviewed_text"])

    version_agent.save_version(
        chapter_id="chapter1",
        version_type="final",
        content=result["final_text"],
        author="human"
    )

    return {
        **state,
        "final_text": result["final_text"]
    }

# Sync node: Retriever
def retriever_node(state: ChapterState) -> ChapterState:
    agent = RetrieverAgent()
    result = agent.retrieve_similar(state["final_text"])

    return {
        **state,
        "retrieval_results": result
    }

# Graph construction
def build_workflow():
    builder = StateGraph(ChapterState)

    builder.add_node("Scrape", scraper_node)
    builder.add_node("Write", writer_node)
    builder.add_node("Review", reviewer_node)
    builder.add_node("HumanReview", human_review_node)
    builder.add_node("Retrieve", retriever_node)

    builder.set_entry_point("Scrape")
    builder.add_edge("Scrape", "Write")
    builder.add_edge("Write", "Review")
    builder.add_edge("Review", "HumanReview")
    builder.add_edge("HumanReview", "Retrieve")

    builder.set_finish_point("Retrieve")

    return builder.compile()