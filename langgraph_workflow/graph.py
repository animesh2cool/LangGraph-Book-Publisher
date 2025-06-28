from langgraph.graph import StateGraph
from typing import TypedDict, Optional
import logging
from agents.scraper_agent import ScraperAgent
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent
from agents.human_review_agent import HumanReviewAgent
from agents.versioning_agent import VersioningAgent
from agents.retriever_agent import RetrieverAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Sync node: Scraper
def scraper_node(state: ChapterState) -> ChapterState:
    try:
        logger.info("Starting scraper node")
        agent = ScraperAgent("https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1")
        result = agent.scrape()
        
        version_agent.save_version(
            chapter_id="chapter1",
            version_type="raw",
            content=result["text"],
            author="scraper"
        )
        
        logger.info("Scraper node completed successfully")
        return {
            **state,
            "raw_text": result["text"],
            "screenshot_path": result["screenshot"]
        }
    except Exception as e:
        logger.error(f"Scraper node error: {e}")
        return {
            **state,
            "raw_text": f"Error during scraping: {str(e)}",
            "screenshot_path": None
        }

# Sync node: Writer
def writer_node(state: ChapterState) -> ChapterState:
    try:
        logger.info("Starting writer node")
        if not state.get("raw_text") or state["raw_text"].startswith("Error"):
            logger.error("Writer node error: No raw text to rewrite")
            return {
                **state,
                "rewritten_text": "Error: No content to rewrite"
            }
        
        agent = WriterAgent()
        result = agent.rewrite(state["raw_text"])
        
        version_agent.save_version(
            chapter_id="chapter1",
            version_type="rewrite",
            content=result["rewritten_text"],
            author="writer"
        )
        
        logger.info("Writer node completed successfully")
        return {
            **state,
            "rewritten_text": result["rewritten_text"]
        }
    except Exception as e:
        logger.error(f"Writer node error: {e}")
        return {
            **state,
            "rewritten_text": f"Error during rewriting: {str(e)}"
        }

# Sync node: Reviewer
def reviewer_node(state: ChapterState) -> ChapterState:
    try:
        logger.info("Starting reviewer node")
        if not state.get("rewritten_text") or state["rewritten_text"].startswith("Error"):
            logger.error("Reviewer node error: No rewritten text to review")
            return {
                **state,
                "reviewed_text": "Error: No content to review"
            }
        
        agent = ReviewerAgent()
        result = agent.review(state["rewritten_text"])
        
        version_agent.save_version(
            chapter_id="chapter1",
            version_type="review",
            content=result["reviewed_text"],
            author="reviewer"
        )
        
        logger.info("Reviewer node completed successfully")
        return {
            **state,
            "reviewed_text": result["reviewed_text"]
        }
    except Exception as e:
        logger.error(f"Reviewer node error: {e}")
        return {
            **state,
            "reviewed_text": f"Error during review: {str(e)}"
        }

# Sync node: Human Review
def human_review_node(state: ChapterState) -> ChapterState:
    try:
        logger.info("Starting human review node")
        if not state.get("reviewed_text") or state["reviewed_text"].startswith("Error"):
            logger.error("Human review node error: No reviewed text for human review")
            return {
                **state,
                "final_text": "Error: No content for human review"
            }
        
        agent = HumanReviewAgent()
        result = agent.review(state["reviewed_text"])
        
        version_agent.save_version(
            chapter_id="chapter1",
            version_type="final",
            content=result["final_text"],
            author="human"
        )
        
        logger.info("Human review node completed successfully")
        return {
            **state,
            "final_text": result["final_text"]
        }
    except Exception as e:
        logger.error(f"Human review node error: {e}")
        return {
            **state,
            "final_text": f"Error during human review: {str(e)}"
        }

# Sync node: Retriever
def retriever_node(state: ChapterState) -> ChapterState:
    try:
        logger.info("Starting retriever node")
        if not state.get("final_text") or state["final_text"].startswith("Error"):
            logger.error("Retriever node error: No final text for retrieval")
            return {
                **state,
                "retrieval_results": {"error": "No content for retrieval"}
            }
        
        agent = RetrieverAgent()
        result = agent.retrieve_similar(state["final_text"])
        
        logger.info("Retriever node completed successfully")
        return {
            **state,
            "retrieval_results": result
        }
    except Exception as e:
        logger.error(f"Retriever node error: {e}")
        return {
            **state,
            "retrieval_results": {"error": f"Error during retrieval: {str(e)}"}
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