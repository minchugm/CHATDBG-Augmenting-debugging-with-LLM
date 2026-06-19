# ai_debug_console/project.py
import os
import json
from typing import Tuple
from .runner import run_subprocess, run_single_file

FRONTEND_PKG = ("react", "vue", "angular")

def collect_project_files(project_path: str) -> Tuple[str, list]:
    all_sources = ""
    found = []
    for root, _, files in os.walk(project_path):
        for f in files:
            if f.endswith((".java", ".py")):
                p = os.path.join(root, f)
                found.append(p)
                try:
                    with open(p, "r", encoding="utf-8") as fh:
                        all_sources += f"\n\n===== {p} =====\n\n" + fh.read()
                except Exception:
                    all_sources += f"\n\n===== {p} =====\n\n<could not read file>"
        if "pom.xml" in files:
            pomp = os.path.join(root, "pom.xml")
            try:
                with open(pomp, "r", encoding="utf-8") as ph:
                    all_sources += f"\n\n===== {pomp} =====\n\n" + ph.read()
            except Exception:
                all_sources += f"\n\n===== {pomp} =====\n\n<could not read file>"
        if "build.gradle" in files or "build.gradle.kts" in files:
            for gradle_file in ("build.gradle", "build.gradle.kts"):
                gp = os.path.join(root, gradle_file)
                if os.path.exists(gp):
                    try:
                        with open(gp, "r", encoding="utf-8") as gh:
                            all_sources += f"\n\n===== {gp} =====\n\n" + gh.read()
                    except Exception:
                        all_sources += f"\n\n===== {gp} =====\n\n<could not read file>"
        if "pyproject.toml" in files:
            pp = os.path.join(root, "pyproject.toml")
            try:
                with open(pp, "r", encoding="utf-8") as ph:
                    all_sources += f"\n\n===== {pp} =====\n\n" + ph.read()
            except Exception:
                all_sources += f"\n\n===== {pp} =====\n\n<could not read file>"
        if "requirements.txt" in files:
            rq = os.path.join(root, "requirements.txt")
            try:
                with open(rq, "r", encoding="utf-8") as rh:
                    all_sources += f"\n\n===== {rq} =====\n\n" + rh.read()
            except Exception:
                all_sources += f"\n\n===== {rq} =====\n\n<could not read file>"
        if ".env" in files:
            try:
                envp = os.path.join(root, ".env")
                with open(envp, "r", encoding="utf-8") as eh:
                    content = eh.read()
                import re
                content = re.sub(r"=(.*)", "=*****", content)
                all_sources += f"\n\n===== {envp} =====\n\n{content}\n"
            except Exception:
                pass
    return all_sources, found

# -----------------------
# Full-project runner (Maven/Gradle/Node/React/Angular/Vue)
# -----------------------
def run_project(path: str, log_callback):
    files = set(os.listdir(path))
    if "pom.xml" in files:
        log_callback("📦 Detected Maven project — running `mvn spring-boot:run` or `mvn exec:java`")
        p = run_subprocess(["mvn", "spring-boot:run"], cwd=path)
        log_callback(p[0] or p[1] or "Maven command finished")
        return p
    if "build.gradle" in files or "build.gradle.kts" in files:
        log_callback("📦 Detected Gradle project — running `./gradlew bootRun` or `gradle run`")
        p = run_subprocess(["./gradlew", "bootRun"], cwd=path, shell=True)
        if p[1]:
            p = run_subprocess(["gradle", "run"], cwd=path)
        log_callback(p[0] or p[1] or "Gradle command finished")
        return p
    # Simple Java project (no Maven/Gradle): compile all .java and run detected main
    java_files = []
    for root, _, fs in os.walk(path):
        for f in fs:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))
    if java_files:
        log_callback(f"☕ Detected simple Java project — compiling {len(java_files)} source files")
        # compile all
        out, err = run_subprocess(["javac", *java_files], cwd=path)
        if err:
            return out, err
        # detect main class (prefer Main.java, else any with main method)
        candidates = []
        try:
            for jf in java_files:
                try:
                    with open(jf, "r", encoding="utf-8") as fh:
                        src = fh.read()
                    has_main = "public static void main(" in src
                    cls = os.path.splitext(os.path.basename(jf))[0]
                    pkg = None
                    for line in src.splitlines():
                        line = line.strip()
                        if line.startswith("package "):
                            pkg = line.split()[1].rstrip(";")
                            break
                    fqcn = f"{pkg}.{cls}" if pkg else cls
                    if has_main:
                        candidates.append((cls.lower() == "main", fqcn))
                except Exception:
                    continue
        except Exception:
            candidates = []
        run_fqcn = None
        if candidates:
            # sort by preference: Main first
            candidates.sort(key=lambda t: (not t[0], t[1]))
            run_fqcn = candidates[0][1]
        else:
            # fallback: try common names
            for name in ("Main", "App", "HelloWorld"):
                for jf in java_files:
                    if os.path.splitext(os.path.basename(jf))[0] == name:
                        try:
                            with open(jf, "r", encoding="utf-8") as fh:
                                src = fh.read()
                            pkg = None
                            for line in src.splitlines():
                                line = line.strip()
                                if line.startswith("package "):
                                    pkg = line.split()[1].rstrip(";")
                                    break
                            run_fqcn = f"{pkg}.{name}" if pkg else name
                            break
                        except Exception:
                            pass
                    if run_fqcn:
                        break
        if not run_fqcn:
            return "", "❌ Could not detect a main class to run. Ensure a class with public static void main(String[] args)."
        log_callback(f"▶️ Running {run_fqcn}")
        return run_subprocess(["java", "-cp", path, run_fqcn], cwd=path)
    py_files = []
    for root, _, fs in os.walk(path):
        for f in fs:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    if any(os.path.exists(os.path.join(path, name)) for name in ("app.py", "manage.py", "pyproject.toml", "requirements.txt")) or py_files:
        log_callback("🐍 Detected Python project — attempting to run")
        app = os.path.join(path, "app.py")
        if os.path.exists(app):
            return run_subprocess(["python", app], cwd=path)
        manage = os.path.join(path, "manage.py")
        if os.path.exists(manage):
            return run_subprocess(["python", manage, "runserver"], cwd=path)
        mains = []
        for pf in py_files:
            try:
                src = open(pf, "r", encoding="utf-8").read()
                if "if __name__ == \"__main__\":" in src:
                    mains.append(pf)
            except Exception:
                pass
        if len(mains) == 1:
            return run_subprocess(["python", mains[0]], cwd=path)
        return "", "No explicit Python run target found. Add app.py or a single script with if __name__ == \"__main__\":"
    return "", "❌ No recognized project files found."
