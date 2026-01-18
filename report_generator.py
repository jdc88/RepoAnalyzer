#!/usr/bin/env python3
"""
report_generator.py

Usage:
  python3 report_generator.py results.json

Output:
  - For each repo: Programming languages, Frameworks & Libraries, Development Tools
  - Final aggregated lists: Languages, Frameworks & Libraries, Development Tools, All detected skills

By the provided repo_skill_scanner.py, this assumes results.json was produced and contains:
  - repo_name
  - languages
  - accepted_skills_by_category
  - possible_skills_by_category
  - candidate_skills_by_category
  - evidence (optional)
"""
import sys
import json
from collections import defaultdict

if len(sys.argv) < 2:
    print("Usage: python3 report_generator.py results.json")
    sys.exit(1)

fn = sys.argv[1]
data = json.load(open(fn, 'r', encoding='utf-8'))

# Categories we treat as "Frameworks & Libraries"
FRAMEWORK_CATEGORIES = {
    "ML/AI", "Web & APIs", "Frontend", "Data & Analysis", "Data & Big Data",
    "Frameworks", "Libraries"
}

# Categories we treat as "Development Tools"
DEVTOOL_CATEGORIES = {
    "Dev Tools", "CI/CD", "Build & Packaging", "Containers & Orchestration",
    "Cloud", "Testing", "Security / Auth", "Databases", "Messaging / Streaming",
    "Performance / GPU", "Serialization / RPC", "Other"
}

# If the scanner used different category names, this set can be expanded.

# Collect aggregated sets
agg_languages = set()
agg_frameworks = set()
agg_devtools = set()
agg_all_skills = set()
agg_possible = set()

def collect_skills_by_categories(skill_map, categories):
    s = set()
    for cat, skills in skill_map.items():
        if cat in categories:
            s.update(skills)
    return s

repos = data.get("repos", [])

print("\nDETAILED PER-REPO REPORT\n" + "="*60)
for r in repos:
    name = r.get("repo_name") or r.get("repo_url")
    print(f"\nRepository: {name}")
    # Languages
    langs = r.get("languages") or []
    print("  Programming languages:")
    if langs:
        for L in langs:
            print("   -", L)
    else:
        print("   - (none detected)")

    agg_languages.update(langs)

    # Accepted skills (strong)
    accepted = r.get("accepted_skills_by_category", {}) or r.get("accepted", {})
    possible = r.get("possible_skills_by_category", {}) or r.get("possible", {})

    frameworks = collect_skills_by_categories(accepted, FRAMEWORK_CATEGORIES)
    devtools = collect_skills_by_categories(accepted, DEVTOOL_CATEGORIES)

    # If accepted is empty for certain categories, include possible as "possible"
    possible_frameworks = collect_skills_by_categories(possible, FRAMEWORK_CATEGORIES)
    possible_devtools = collect_skills_by_categories(possible, DEVTOOL_CATEGORIES)

    # Print frameworks & libraries
    print("  Frameworks & Libraries (confirmed):")
    if frameworks:
        for f in sorted(frameworks):
            print("   -", f)
    else:
        print("   - (none confirmed)")

    if possible_frameworks:
        print("  Frameworks & Libraries (possible/unconfirmed):")
        for f in sorted(possible_frameworks):
            print("   -", f)

    # Print dev tools
    print("  Development tools (confirmed):")
    if devtools:
        for d in sorted(devtools):
            print("   -", d)
    else:
        print("   - (none confirmed)")

    if possible_devtools:
        print("  Development tools (possible/unconfirmed):")
        for d in sorted(possible_devtools):
            print("   -", d)

    # Add to aggregates
    agg_frameworks.update(frameworks)
    agg_devtools.update(devtools)
    agg_all_skills.update(frameworks)
    agg_all_skills.update(devtools)
    # also include accepted skills from all categories
    for cat, skills in (accepted or {}).items():
        agg_all_skills.update(skills)
    for cat, skills in (possible or {}).items():
        agg_possible.update(skills)

print("\n" + "="*60)
print("AGGREGATED SUMMARY (ACROSS ALL REPOS)\n")

print("Programming languages:")
if agg_languages:
    for L in sorted(agg_languages):
        print(" -", L)
else:
    print(" - (none detected)")

print("\nFrameworks & Libraries (confirmed):")
if agg_frameworks:
    for f in sorted(agg_frameworks):
        print(" -", f)
else:
    print(" - (none detected)")

print("\nDevelopment tools (confirmed):")
if agg_devtools:
    for d in sorted(agg_devtools):
        print(" -", d)
else:
    print(" - (none detected)")

# Everything used (confirmed + possible)
# all_used = set(agg_all_skills) | set(agg_possible)
# print("\nEverything detected (confirmed + possible/unconfirmed):")
# if all_used:
#     for s in sorted(all_used):
#         print(" -", s)
# else:
#     print(" - (none detected)")

print("\nReport generation complete.")