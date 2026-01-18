#!/usr/bin/env python3
"""
repo_skill_scanner.py

Usage:
    python3 repo_skill_scanner.py repos.txt results.json
Input:
  - repos.txt: Text file with one Git repository URL pasted per line.
Output:
  - results.json: JSON file with detailed scan results per repo and aggregated skills.

Notes:
  - The script performs shallow clones (--depth 1) for speed.
  - The script converts any sets to lists before writing JSON so json.dump won't fail.
  - Python 3.8+ recommended.
"""
import sys                  # Access to command-line arguments (sys.argv) and exit handling
import os                   # Operating system interfaces (os.walk, os.path)
import subprocess           # Running git commands (subprocess.run)
import tempfile             # Temporary directory creation (tempfile.mkdtemp)
import json                 # JSON serialization (json.dump)
import shutil               # File operations (shutil.rmtree)
import re                   # Regular expressions (re module)
from pathlib import Path    # Path manipulations (Path)

# Create hash maps: token -> (label, category)

PACKAGE_KEYWORD_MAP = {
    # =============== Cloud & DevOps ===============
    "boto3": ("AWS (boto3)", "Cloud"),
    "aws": ("AWS", "Cloud"),
    "aws-sdk": ("AWS SDK (Node.js)", "Cloud"),
    "azure": ("Azure", "Cloud"),
    "google-cloud": ("Google Cloud", "Cloud"),
    "pulumi": ("Pulumi", "Cloud / IaC"),
    "terraform": ("Terraform", "Cloud / IaC"),
    "kubernetes": ("Kubernetes", "Containers / Orchestration"),
    "helm": ("Helm", "Containers / Orchestration"),

    # =============== Backend / APIs ===============
    "flask": ("Flask", "Web & APIs"),
    "fastapi": ("FastAPI", "Web & APIs"),
    "django": ("Django", "Web & APIs"),
    "express": ("Express.js", "Web & APIs"),
    "nestjs": ("NestJS", "Web & APIs"),
    "spring": ("Spring Framework", "Web & APIs"),
    "springboot": ("Spring Boot", "Web & APIs"),
    "grpc": ("gRPC", "Web & APIs"),

    # =============== Frontend ===============
    "react": ("React", "Frontend"),
    "react-dom": ("React", "Frontend"),
    "next": ("Next.js", "Frontend"),
    "vue": ("Vue.js", "Frontend"),
    "angular": ("Angular", "Frontend"),
    "svelte": ("Svelte", "Frontend"),
    "axios": ("axios (HTTP client)", "Frontend"),
    "redux": ("Redux", "Frontend"),
    "tailwind": ("Tailwind CSS", "Frontend"),
    "bootstrap": ("Bootstrap", "Frontend"),

    # =============== Data & ML ===============
    "numpy": ("NumPy", "Data & Analysis"),
    "pandas": ("Pandas", "Data & Analysis"),
    "scipy": ("SciPy", "Data & Analysis"),
    "sklearn": ("scikit-learn", "ML/AI"),
    "xgboost": ("XGBoost", "ML/AI"),
    "lightgbm": ("LightGBM", "ML/AI"),
    "tensorflow": ("TensorFlow", "ML/AI"),
    "torch": ("PyTorch", "ML/AI"),
    "keras": ("Keras", "ML/AI"),
    "opencv": ("OpenCV", "Computer Vision"),
    "transformers": ("Hugging Face Transformers", "ML/AI"),

    # =============== Databases ===============
    "sqlalchemy": ("SQLAlchemy", "Databases"),
    "psycopg2": ("PostgreSQL", "Databases"),
    "mysql": ("MySQL", "Databases"),
    "pymongo": ("MongoDB", "Databases"),
    "redis": ("Redis", "Databases"),
    "elasticsearch": ("Elasticsearch", "Databases / Search"),

    # =============== Messaging / Streaming ===============
    "kafka": ("Apache Kafka", "Streaming"),
    "pulsar": ("Apache Pulsar", "Streaming"),
    "rabbitmq": ("RabbitMQ", "Messaging"),

    # =============== Testing ===============
    "pytest": ("pytest", "Testing"),
    "unittest": ("unittest", "Testing"),
    "jest": ("Jest", "Testing"),
    "mocha": ("Mocha", "Testing"),
    "cypress": ("Cypress", "Testing"),

    # =============== Observability ===============
    "prometheus": ("Prometheus", "Observability"),
    "grafana": ("Grafana", "Observability"),
    "opentelemetry": ("OpenTelemetry", "Observability"),

    # =============== Security ===============
    "jwt": ("JWT Authentication", "Security"),
    "oauth": ("OAuth", "Security"),
    "bcrypt": ("bcrypt", "Security"),

    # =============== GUI / Desktop Apps ===============
    "tkinter": ("Tkinter", "GUI / Desktop"),
    "pyqt5": ("PyQt5", "GUI / Desktop"),
    "pyqt": ("PyQt", "GUI / Desktop"),
    "pyside2": ("PySide2", "GUI / Desktop"),
    "pyside6": ("PySide6", "GUI / Desktop"),
    "wx": ("wxPython", "GUI / Desktop"),
    "kivy": ("Kivy", "GUI / Desktop"),

}

KEYWORD_MAP = {
    # =============== CI/CD ===============
    ".github/workflows": ("GitHub Actions (CI/CD)", "CI/CD"),
    "gitlab-ci": ("GitLab CI", "CI/CD"),
    "jenkins": ("Jenkins", "CI/CD"),
    "circleci": ("CircleCI", "CI/CD"),
    "azure-pipelines": ("Azure Pipelines", "CI/CD"),

    # =============== Infrastructure ===============
    "terraform": ("Terraform", "Cloud / IaC"),
    "cloudformation": ("AWS CloudFormation", "Cloud / IaC"),
    "pulumi": ("Pulumi", "Cloud / IaC"),

    # =============== Containers / Orchestration ===============
    "kubernetes": ("Kubernetes", "Containers / Orchestration"),
    "k8s": ("Kubernetes", "Containers / Orchestration"),
    "helm": ("Helm", "Containers / Orchestration"),

    # =============== Performance / GPU ===============
    "cuda": ("CUDA / NVIDIA (GPU)", "Performance / GPU"),
    "nvidia": ("NVIDIA / CUDA (GPU)", "Performance / GPU"),
    "openmp": ("OpenMP", "Performance"),
    "mpi": ("MPI", "Performance"),

    # =============== Data / Analytics ===============
    "spark": ("Apache Spark", "Data Engineering"),
    "hadoop": ("Hadoop", "Data Engineering"),
    "airflow": ("Apache Airflow", "Data Engineering"),
    "dbt": ("dbt", "Data Engineering"),

    # =============== Security ===============
    "oauth": ("OAuth", "Security"),
    "openid": ("OpenID Connect", "Security"),
    "saml": ("SAML", "Security"),

    # =============== GUI / Desktop ===============
    "tkinter": ("Tkinter", "GUI / Desktop"),
    "pyqt5": ("PyQt5", "GUI / Desktop"),
    "pyside": ("PySide", "GUI / Desktop"),
    "wxpython": ("wxPython", "GUI / Desktop"),
    "kivy": ("Kivy", "GUI / Desktop"),

}

MANIFEST_FILES = {
    # Python
    "requirements.txt", "requirements-dev.txt",
    "environment.yml", "environment.yaml",
    "pyproject.toml", "setup.py", "setup.cfg", "poetry.lock",

    # Node
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",

    # Java / JVM
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",

    # Go
    "go.mod", "go.sum",

    # Rust
    "cargo.toml", "cargo.lock",

    # Ruby
    "gemfile", "gemfile.lock",

    # .NET
    "csproj", "fsproj", "packages.config",

    # PHP
    "composer.json", "composer.lock",

    # Mobile
    "podfile", "podfile.lock",
}

EXT_LANG_MAP = {
    ".py": "Python",
    ".ipynb": "Jupyter Notebook",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".rs": "Rust",
    ".go": "Go",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".scala": "Scala",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".tf": "Terraform",
    ".md": "Markdown",
    ".sh": "Shell",
}

# Regex helpers
IMPORT_RE_PY = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', re.MULTILINE)
IMPORT_RE_JAVA = re.compile(r'^\s*import\s+([a-zA-Z0-9_\.]+);', re.MULTILINE)
INCLUDE_RE_C = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.MULTILINE)

# SKIP_FILENAMES = {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}

def keyword_present(key, text):
    if len(key) <= 4:
        return re.search(rf"\b{re.escape(key)}\b", text) is not None
    return key in text


def safe_read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def extract_imports_from_py(content):
    return {m.split(".")[0] for m in IMPORT_RE_PY.findall(content)}


def normalize_js_pkg(name):
    return name if name.startswith("@") else name.split("/")[0]


def extract_imports_from_js(content):
    pkgs = set()
    for m in re.findall(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', content):
        pkgs.add(normalize_js_pkg(m))
    for m in re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content):
        pkgs.add(normalize_js_pkg(m))
    return pkgs


def extract_imports_from_java(content):
    return {m.split(".")[0].lower() for m in IMPORT_RE_JAVA.findall(content)}


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, set):
        return sorted(make_json_safe(v) for v in obj)
    return obj


def map_token_to_skill(token):
    tl = token.lower()
    results = []
    for key, (label, category) in PACKAGE_KEYWORD_MAP.items():
        if tl == key or tl.startswith((key + "-", key + "_", key + ".")):
            results.append((label, category))
    for key, (label, category) in KEYWORD_MAP.items():
        if key in tl:
            results.append((label, category))
    return results


def scan_repo(repo_url, dest_dir):
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target = os.path.join(dest_dir, repo_name)

    result = {
        "repo_url": repo_url,
        "repo_name": repo_name,
        "cloned": False,
        "errors": [],
        "languages": set(),
        "packages_found": {},
        "imports_found": set(),
        "manifest_tokens": set(),
        "file_extensions": set(),
        "file_paths": [],
        "candidate_skills_by_category": {},
        "accepted_skills_by_category": {},
        "possible_skills_by_category": {},
        "evidence": {},
        "files_scanned": 0,
    }

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, target],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result["cloned"] = True
    except subprocess.CalledProcessError as e:
        result["errors"].append(str(e))
        return result

    all_content = []

    for root, dirs, files in os.walk(target):
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            # if filename.lower() in SKIP_FILENAMES:
            #     continue

            result["files_scanned"] += 1
            path = os.path.join(root, filename)
            rel = os.path.relpath(path, target)
            rel_l = rel.replace("\\", "/").lower()
            result["file_paths"].append(rel_l)

            ext = Path(filename).suffix.lower()
            if ext:
                result["file_extensions"].add(ext)
                if ext in EXT_LANG_MAP:
                    result["languages"].add(EXT_LANG_MAP[ext])

            content = safe_read(path)
            content_l = content.lower()
            all_content.append(content_l)

            if filename.lower() in MANIFEST_FILES:
                for tk in re.findall(r"[a-zA-Z0-9_\-.]+", content_l): 
                    result["manifest_tokens"].add(tk)
                    result["packages_found"].setdefault(tk, []).append(rel)
                result["evidence"].setdefault("manifests", []).append(rel)

            if ext == ".py":
                for pkg in extract_imports_from_py(content):
                    result["imports_found"].add(pkg)
                    result["packages_found"].setdefault(pkg, []).append(rel)

            if ext in (".js", ".ts", ".jsx", ".tsx"):
                for pkg in extract_imports_from_js(content):
                    result["imports_found"].add(pkg)
                    result["packages_found"].setdefault(pkg, []).append(rel)

            if ext == ".java":
                for pkg in extract_imports_from_java(content):
                    result["imports_found"].add(pkg)
                    result["packages_found"].setdefault(pkg, []).append(rel)

            if ext in (".c", ".h", ".cpp", ".cc", ".cxx"):
                for m in INCLUDE_RE_C.findall(content):
                    tok = m.split(".")[0].lower()
                    result["packages_found"].setdefault(tok, []).append(rel)

            for key, (label, _) in KEYWORD_MAP.items():
                if keyword_present(key, content_l) or keyword_present(key, rel_l):
                    result["packages_found"].setdefault(key, []).append(rel)
                    result["evidence"].setdefault(label, []).append(rel)

            for key, (label, _) in PACKAGE_KEYWORD_MAP.items():
                if keyword_present(key, content_l) or keyword_present(key, rel_l):
                    result["packages_found"].setdefault(key, []).append(rel)
                    result["evidence"].setdefault(label, []).append(rel)

    for k, v in result["evidence"].items():
        result["evidence"][k] = sorted(set(v))

    repo_content = "\n".join(all_content)

    all_tokens = (
        {k.lower() for k in result["packages_found"]}
        | {t.lower() for t in result["imports_found"]}
        | {t.lower() for t in result["manifest_tokens"]}
    )

    candidate_skills = {}
    candidate_mappings = {}

    for token in all_tokens:
        for label, category in map_token_to_skill(token):
            candidate_skills.setdefault(category, set()).add(label)
            candidate_mappings.setdefault(token, (label, category))

    accepted, possible = {}, {}

    for token, (label, category) in candidate_mappings.items():
        seen = (
            token in map(str.lower, result["imports_found"])
            or token in map(str.lower, result["manifest_tokens"])
            or len(set(result["packages_found"].get(token, []))) >= 2
        )
        (accepted if seen else possible).setdefault(category, set()).add(label)

    result["candidate_skills_by_category"] = {k: sorted(v) for k, v in candidate_skills.items()}
    result["accepted_skills_by_category"] = {k: sorted(v) for k, v in accepted.items()}
    result["possible_skills_by_category"] = {k: sorted(v) for k, v in possible.items()}
    result["languages"] = sorted(result["languages"])
    result["packages_found"] = {k: sorted(set(v)) for k, v in result["packages_found"].items()}
    result["imports_found"] = sorted(result["imports_found"])
    result["manifest_tokens"] = sorted(result["manifest_tokens"])

    return result


def aggregate_results(repo_results):
    agg = {}
    for r in repo_results:
        for cat, skills in r.get("accepted_skills_by_category", {}).items():
            agg.setdefault(cat, set()).update(skills)
    return {k: sorted(v) for k, v in agg.items()}


def generate_resume_bullets(agg):
    return [f"{cat}: {', '.join(skills)}." for cat, skills in agg.items()]


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 repo_skill_scanner.py repos.txt results.json")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        repos = [l.strip() for l in f if l.strip()]

    workspace = tempfile.mkdtemp(prefix="repo-scan-")
    results = {"repos": [], "aggregated": {}, "summary": {}}

    try:
        for repo in repos:
            print("Scanning:", repo)
            results["repos"].append(scan_repo(repo, workspace))

        results["aggregated"] = aggregate_results(results["repos"])
        results["summary"]["resume_bullets"] = generate_resume_bullets(results["aggregated"])

        with open(sys.argv[2], "w", encoding="utf-8") as f:
            json.dump(make_json_safe(results), f, indent=2)

        print("\nScan complete.")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    main()
