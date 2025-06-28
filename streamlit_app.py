import streamlit as st
import sys
import os
import logging
import time

# Fix for PyTorch/Streamlit compatibility issue
import warnings
warnings.filterwarnings("ignore", message=".*torch.classes.*")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import your workflow after fixing torch issues
try:
    from langgraph_workflow.graph import build_workflow, ChapterState
    from agents.scraper_agent import ScraperAgent
    from agents.writer_agent import WriterAgent
    from agents.reviewer_agent import ReviewerAgent
    from agents.human_review_agent import HumanReviewAgent
    from agents.retriever_agent import RetrieverAgent
    from agents.versioning_agent import VersioningAgent
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure your modules are properly installed and accessible.")
    st.stop()

def run_step_with_display(step_name, step_func, state, step_container, text_container):
    """Run a workflow step and display results in real-time"""
    with step_container:
        st.info(f"🔄 Processing: {step_name}")
    
    # Execute the step
    try:
        result_state = step_func(state)
        
        with step_container:
            st.success(f"✅ Completed: {step_name}")
        
        # Display the text result immediately
        display_step_result(step_name, result_state, text_container)
        
        return result_state
        
    except Exception as e:
        with step_container:
            st.error(f"❌ Failed: {step_name} - {str(e)}")
        return state

def display_step_result(step_name, state, container):
    """Display the result of each step in the text container"""
    with container:
        if step_name == "Scraper":
            if state.get("raw_text"):
                st.subheader("🔍 1. Raw Scraped Content")
                # Calculate height based on content
                text_height = max(300, min(800, len(state["raw_text"]) // 5))
                st.text_area("Raw Content", state["raw_text"], height=text_height, key=f"raw_{time.time()}", disabled=True)
                if state.get("screenshot_path"):
                    st.caption(f"📸 Screenshot: {state['screenshot_path']}")
                st.divider()
                
        elif step_name == "Writer":
            if state.get("rewritten_text"):
                st.subheader("✍️ 2. AI Rewritten Content")
                text_height = max(300, min(800, len(state["rewritten_text"]) // 5))
                st.text_area("Rewritten Content", state["rewritten_text"], height=text_height, key=f"rewritten_{time.time()}", disabled=True)
                st.divider()
                
        elif step_name == "Reviewer":
            if state.get("reviewed_text"):
                st.subheader("📝 3. AI Reviewed Content")
                text_height = max(300, min(800, len(state["reviewed_text"]) // 5))
                st.text_area("Reviewed Content", state["reviewed_text"], height=text_height, key=f"reviewed_{time.time()}", disabled=True)
                st.divider()
                
        elif step_name == "Human Review":
            st.subheader("👤 4. Human Review Required")
            if state.get("reviewed_text"):
                st.markdown("**Content ready for human review:**")
                text_height = max(300, min(800, len(state["reviewed_text"]) // 5))
                st.text_area("Content to Review", state["reviewed_text"], height=text_height, key=f"review_display_{time.time()}", disabled=True)
                
                # Only show review options if human review is not complete
                if not st.session_state.get("human_review_complete"):
                    # Human review options
                    st.markdown("**Choose your review action:**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("✅ Submit Without Changes", key="submit_unchanged", type="primary", use_container_width=True):
                            st.session_state.human_review_decision = "unchanged"
                            st.session_state.final_content = state["reviewed_text"]
                            st.session_state.human_review_complete = True
                            st.success("Content approved without changes!")
                            st.rerun()
                    
                    with col2:
                        if st.button("✏️ Submit Revised Content", key="submit_revised", type="secondary", use_container_width=True):
                            st.session_state.human_review_decision = "revise"
                    
                    # Show revision area if user chose to revise
                    if st.session_state.get("human_review_decision") == "revise":
                        st.markdown("**Enter your revised content:**")
                        revised_content = st.text_area(
                            "Revised Content", 
                            value=state["reviewed_text"], 
                            height=text_height,
                            key="revision_area",
                            help="Edit the content as needed and click 'Confirm Revision' when done"
                        )
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            if st.button("💾 Confirm Revision", key="confirm_revision", type="primary", use_container_width=True):
                                st.session_state.final_content = revised_content
                                st.session_state.human_review_complete = True
                                st.success("Revision confirmed!")
                                st.rerun()
                        
                        with col4:
                            if st.button("↩️ Cancel Revision", key="cancel_revision", use_container_width=True):
                                st.session_state.human_review_decision = None
                                st.rerun()
                
                # Display final content if human review is complete
                if st.session_state.get("human_review_complete"):
                    st.markdown("**Final Human-Reviewed Content:**")
                    final_content = st.session_state.get("final_content", state["reviewed_text"])
                    final_height = max(300, min(800, len(final_content) // 5))
                    st.text_area("Final Content", final_content, height=final_height, key=f"final_{time.time()}", disabled=True)
                    
                    if st.session_state.get("human_review_decision") == "revise":
                        st.info("✏️ Content was revised by human reviewer")
                    else:
                        st.info("✅ Content approved without changes")
                
                st.divider()
                
        elif step_name == "Retriever":
            if state.get("retrieval_results"):
                st.subheader("🔎 5. Retrieval Results")
                st.json(state["retrieval_results"])
                st.divider()

def main():
    st.set_page_config(page_title="Live LangGraph Processor", layout="wide")
    
    st.title("📚 AI BOOK PUBLICATION")
    st.markdown("Watch the AI agents process content in real-time: **Scraper → Writer → Reviewer → Human Review → Retriever**")
    
    # Initialize session state variables
    if 'processing_started' not in st.session_state:
        st.session_state.processing_started = False
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = {}
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("⚙️ Configuration")
        url_input = st.text_input(
            "Source URL", 
            value="https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1",
            help="URL to scrape content from"
        )
        
        st.divider()
        
        if st.button("🚀 Start Live Processing", type="primary", use_container_width=True):
            # Reset all processing-related session state
            st.session_state.processing_started = True
            st.session_state.current_step = 0
            st.session_state.url = url_input
            st.session_state.processing_complete = False
            st.session_state.human_review_complete = False
            st.session_state.human_review_decision = None
            st.session_state.final_content = None
            st.session_state.workflow_state = {}
            st.session_state.steps_executed = set()  # Reset step execution tracking
            st.rerun()
        
        if st.button("🔄 Reset", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Show current session state for debugging (optional)
        if st.checkbox("Show Debug Info"):
            st.json({
                "processing_started": st.session_state.get("processing_started", False),
                "current_step": st.session_state.get("current_step", 0),
                "human_review_decision": st.session_state.get("human_review_decision"),
                "human_review_complete": st.session_state.get("human_review_complete", False),
                "has_final_content": bool(st.session_state.get("final_content"))
            })
    
    # Main processing area
    if not st.session_state.get('processing_started', False):
        st.info("👈 **Configure the URL and click 'Start Live Processing' to see the workflow in action**")
        st.markdown("""
        ### What you'll see:
        1. **🔍 Raw Content** - Direct scraping from the source
        2. **✍️ Rewritten Content** - AI-improved version
        3. **📝 Reviewed Content** - Quality-checked text
        4. **👤 Human Review** - Final human oversight
        5. **🔎 Retrieval Results** - Similar content findings
        """)
        return
    
    # Processing logic
    if st.session_state.processing_started and not st.session_state.get('processing_complete', False):
        
        # Create layout for live updates
        progress_col, status_col = st.columns([3, 1])
        
        with progress_col:
            st.subheader("📊 Processing Progress")
            progress_bar = st.progress(0)
            
        with status_col:
            st.subheader("🎯 Current Status")
            status_container = st.empty()
        
        # Container for step-by-step results
        st.subheader("📝 Live Processing Results")
        results_container = st.container()
        
        # Initialize versioning agent (only once)
        if 'version_agent' not in st.session_state:
            st.session_state.version_agent = VersioningAgent()
        
        # Initialize step execution tracking
        if 'steps_executed' not in st.session_state:
            st.session_state.steps_executed = set()
        
        # Define workflow steps with functions
        def scraper_step(state):
            if "scraper" in st.session_state.steps_executed:
                return state
            agent = ScraperAgent(st.session_state.url)
            result = agent.scrape()
            st.session_state.version_agent.save_version("chapter1", "raw", result["text"], "scraper")
            st.session_state.steps_executed.add("scraper")
            return {**state, "raw_text": result["text"], "screenshot_path": result["screenshot"]}
        
        def writer_step(state):
            if "writer" in st.session_state.steps_executed:
                return state
            if not state.get("raw_text"):
                raise Exception("No raw text available")
            agent = WriterAgent()
            result = agent.rewrite(state["raw_text"])
            st.session_state.version_agent.save_version("chapter1", "rewrite", result["rewritten_text"], "writer")
            st.session_state.steps_executed.add("writer")
            return {**state, "rewritten_text": result["rewritten_text"]}
        
        def reviewer_step(state):
            if "reviewer" in st.session_state.steps_executed:
                return state
            if not state.get("rewritten_text"):
                raise Exception("No rewritten text available")
            agent = ReviewerAgent()
            result = agent.review(state["rewritten_text"])
            st.session_state.version_agent.save_version("chapter1", "review", result["reviewed_text"], "reviewer")
            st.session_state.steps_executed.add("reviewer")
            return {**state, "reviewed_text": result["reviewed_text"]}
        
        def human_review_step(state):
            if not state.get("reviewed_text"):
                raise Exception("No reviewed text available")
            
            # Check if human review is complete
            if st.session_state.get("human_review_complete"):
                # Use the final content from human review
                final_content = st.session_state.get("final_content", state["reviewed_text"])
                # Save version (only once)
                if "human_review" not in st.session_state.steps_executed:
                    st.session_state.version_agent.save_version("chapter1", "final", final_content, "human")
                    st.session_state.steps_executed.add("human_review")
                return {**state, "final_text": final_content}
            else:
                # Return state without modification, human review is handled in UI
                return state
        
        def retriever_step(state):
            if "retriever" in st.session_state.steps_executed:
                return state
            if not state.get("final_text"):
                raise Exception("No final text available")
            agent = RetrieverAgent()
            result = agent.retrieve_similar(state["final_text"])
            st.session_state.steps_executed.add("retriever")
            return {**state, "retrieval_results": result}
        
        # Workflow steps
        steps = [
            ("Scraper", scraper_step, 20),
            ("Writer", writer_step, 40),
            ("Reviewer", reviewer_step, 60),
            ("Human Review", human_review_step, 80),
            ("Retriever", retriever_step, 100)
        ]
        
        # Initialize state from session state or create new
        current_state = st.session_state.workflow_state.copy() if st.session_state.workflow_state else {}
        
        # Process steps up to current step
        for i, (step_name, step_func, progress_value) in enumerate(steps):
            if i < st.session_state.current_step:
                # Step already completed, just display
                display_step_result(step_name, current_state, results_container)
                progress_bar.progress(progress_value)
            elif i == st.session_state.current_step:
                # Current step to process
                if step_name == "Human Review":
                    # Display the human review interface
                    display_step_result(step_name, current_state, results_container)
                    
                    # Check if human review is complete
                    if st.session_state.get("human_review_complete"):
                        # Process the human review step
                        current_state = run_step_with_display(
                            step_name, 
                            step_func, 
                            current_state, 
                            status_container, 
                            results_container
                        )
                        st.session_state.workflow_state = current_state
                        st.session_state.current_step += 1
                        progress_bar.progress(progress_value)
                        st.rerun()
                    else:
                        # Wait for human review
                        with status_container:
                            st.warning("⏳ Waiting for human review...")
                        progress_bar.progress(progress_value - 20)
                        break
                else:
                    # Regular step processing
                    current_state = run_step_with_display(
                        step_name, 
                        step_func, 
                        current_state, 
                        status_container, 
                        results_container
                    )
                    st.session_state.workflow_state = current_state
                    st.session_state.current_step += 1
                    progress_bar.progress(progress_value)
                    
                    # Add delay for visual effect (except for human review step)
                    if step_name != "Human Review":
                        time.sleep(0.5)
                    
                    # If not the last step, rerun to continue
                    if i < len(steps) - 1:
                        st.rerun()
                break
            else:
                # Future steps, don't process yet
                break
        
        # Check if all steps are complete
        if st.session_state.current_step >= len(steps):
            # Final status
            with status_container:
                st.success("🎉 All Steps Completed!")
            
            # Summary metrics
            st.subheader("📊 Processing Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                raw_len = len(current_state.get("raw_text", "") or "")
                st.metric("Raw Text", f"{raw_len:,} chars")
            with col2:
                rewritten_len = len(current_state.get("rewritten_text", "") or "")
                st.metric("Rewritten", f"{rewritten_len:,} chars")
            with col3:
                # Fix the TypeError by ensuring we get a string before calling len()
                final_text = current_state.get("final_text", "")
                if not final_text:
                    final_text = st.session_state.get("final_content", "")
                final_len = len(str(final_text)) if final_text else 0
                st.metric("Final Text", f"{final_len:,} chars")
            with col4:
                retrieval_results = current_state.get("retrieval_results", {})
                similar_count = len(retrieval_results.get("similar_content", []) if isinstance(retrieval_results, dict) else [])
                st.metric("Similar Docs", similar_count)
            
            # Mark processing as complete
            st.session_state.processing_complete = True

if __name__ == "__main__":
    main()