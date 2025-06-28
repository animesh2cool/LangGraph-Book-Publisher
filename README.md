# AI Book Publication Workflow

An end-to-end automated system for AI-assisted book publishing. It uses web scraping, AI rewriting, review agents, and human-in-the-loop final editing — all orchestrated with **LangGraph**, **FastAPI**, and an interactive **Bootstrap** UI.

---

##  Features

 **Web Scraping** — Fetch chapters and screenshots from online sources.  
 **AI Rewriting** — Automatically rewrite the raw content using LLMs.  
 **AI Review** — Review and refine the rewritten content.  
 **Human Editing** — Final review and submission by a human.  
 **Version Control** — All intermediate versions are saved with timestamp & user.  
 **Progress Tracker** — Interactive UI showing each step as completed.

---

## Install Dependencies

pip install -r requirements.txt

Also install Playwright browser: playwright install

---

## Tech Stack
LangGraph — Agent-based execution flow

FastAPI — Backend framework

Bootstrap 5 — UI styling

Playwright — Web scraping with screenshots

ChromaDB — Version retrieval and semantic memory

---
