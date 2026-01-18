# RepoAnalyzer 

## Description
RepoAnalyzer is a terminal-based Python tool that analyzes GitHub repositories and automatically infers technical skills based on the codebase. It performs shallow Git clones of repositories, scans source files, manifests, and imports, and produces a structured JSON report summarizing detected programming languages, frameworks, tools, and technologies.

This tool is especially useful for:
- Auditing/Scanning GitHub projects for resume-ready skills
- Automatically extracting tech stacks from multiple repositories
- Gaining insight into the technologies used across codebases

---

## Features
- Shallow clones repositories for fast analysis
- Detects programming languages via file extensions
- Extracts packages from imports and dependency manifests
- Maps detected tokens to categorized technical skills
- Differentiates between **accepted** and **possible** skills
- Generates aggregated skill summaries and resume bullet points
- Outputs detailed results in JSON format by running the repo_skill_scanner.py file first then summarization through report_generator.py

---

## Technologies Used
- Python 3.8+
- Git (via subprocess)
- Regular Expressions
- JSON serialization
- Temporary filesystem management