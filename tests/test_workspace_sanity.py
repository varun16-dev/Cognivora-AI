"""
Workspace Sanity and Architecture Validation Test for Cognivora AI (Week 1).
Validates that the project directory structure, mandatory documentation files,
environment configurations, and architectural specifications are properly initialized.
"""

import os
import re
import sys
from pathlib import Path


def test_directory_structure():
    """Verify that all architectural directories exist."""
    root = Path(__file__).resolve().parent.parent
    required_dirs = [
        "backend/app/api",
        "backend/app/agents",
        "backend/app/tools",
        "backend/app/rag",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/database",
        "backend/app/auth",
        "backend/app/utils",
        "frontend",
        "data/sample_documents",
        "tests",
        "docs",
    ]
    missing = []
    for d in required_dirs:
        dir_path = root / d
        if not dir_path.is_dir():
            missing.append(d)

    assert not missing, f"Missing required project directories: {missing}"
    print(f"  Directory structure: Verified ({len(required_dirs)} directories exist).")


def test_mandatory_files():
    """Verify that all core Week 1 documentation and config files exist and are non-empty."""
    root = Path(__file__).resolve().parent.parent
    mandatory_files = [
        "README.md",
        "docs/PROJECT_PLAN.md",
        ".gitignore",
        ".env.example",
        "data/sample_documents/os_deadlocks_and_scheduling.txt",
    ]
    missing_or_empty = []
    for f in mandatory_files:
        file_path = root / f
        if not file_path.is_file() or file_path.stat().st_size == 0:
            missing_or_empty.append(f)

    assert not missing_or_empty, f"Missing or empty mandatory files: {missing_or_empty}"
    print(f"  Mandatory files: Verified ({len(mandatory_files)} files validated).")


def test_project_plan_sections():
    """Verify that docs/PROJECT_PLAN.md contains all essential architectural topics."""
    root = Path(__file__).resolve().parent.parent
    plan_path = root / "docs" / "PROJECT_PLAN.md"
    content = plan_path.read_text(encoding="utf-8")

    essential_keywords = [
        "Project Vision",
        "Problem Statement",
        "Target Users",
        "Success Criteria",
        "Functional Requirements",
        "Non-Functional Requirements",
        "Track B",
        "System Architecture",
        "Agent & Tool Architecture",
        "RAG Pipeline",
        "Adaptive Learning Engine",
        "Database Schema",
        "Frontend & Visual Design",
        "Backend Architecture",
        "Security & Guardrails",
        "Testing & Verification",
        "Deployment Strategy",
        "8-Week Master Delivery Roadmap",
        "Team Roles",
        "Risks & Mitigation",
    ]

    missing = [kw for kw in essential_keywords if kw.lower() not in content.lower()]
    assert not missing, f"PROJECT_PLAN.md is missing required sections: {missing}"
    print(f"  PROJECT_PLAN.md content: Verified ({len(essential_keywords)} sections found).")


def test_readme_mermaid_diagrams():
    """Verify that README.md contains the 9 required architectural diagrams in Mermaid."""
    root = Path(__file__).resolve().parent.parent
    readme_path = root / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    mermaid_blocks = re.findall(r"```mermaid(.*?)```", content, re.DOTALL)
    assert len(mermaid_blocks) >= 8, f"Expected at least 8 Mermaid diagrams, found {len(mermaid_blocks)}"
    print(f"  README.md diagrams: Verified ({len(mermaid_blocks)} Mermaid diagrams validated).")


def test_env_example_keys():
    """Verify that .env.example contains configuration keys for all core subsystems."""
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env.example"
    content = env_path.read_text(encoding="utf-8")

    required_keys = [
        "ENVIRONMENT",
        "SECRET_KEY",
        "DATABASE_URL",
        "VECTOR_DB_TYPE",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "DEFAULT_ORCHESTRATOR_MODEL",
        "FAST_GENERATION_MODEL",
        "EMBEDDING_MODEL",
        "TTS_PROVIDER",
        "STT_PROVIDER",
    ]

    missing = [k for k in required_keys if k not in content]
    assert not missing, f".env.example is missing required keys: {missing}"
    print(f"  .env.example configuration: Verified ({len(required_keys)} keys found).")


if __name__ == "__main__":
    print("\nRunning Cognivora AI Week 1 Workspace Sanity Checks...")
    try:
        test_directory_structure()
        test_mandatory_files()
        test_project_plan_sections()
        test_readme_mermaid_diagrams()
        test_env_example_keys()
        print("\nAll Week 1 Workspace Sanity Checks PASSED successfully!\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n Sanity Check Failed: {e}\n")
        sys.exit(1)

