import os
import subprocess
import threading

def _stream_process(proc, cb):
    for line in iter(proc.stdout.readline, ""):
        if line:
            cb(line.rstrip())
    proc.stdout.close()

def run_cmd(command, cwd, cb):
    proc = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
    t = threading.Thread(target=_stream_process, args=(proc, cb), daemon=True)
    t.start()
    return proc

def detect_and_run(project_path: str, cb):
    files = os.listdir(project_path)
    # Maven
    if "pom.xml" in files:
        cb("📦 Detected Maven project (running 'mvn spring-boot:run' where appropriate)")
        return run_cmd("mvn spring-boot:run", project_path, cb)

    # Gradle
    if "build.gradle" in files or "build.gradle.kts" in files:
        cb("📦 Detected Gradle project (running './gradlew bootRun' or 'gradle run')")
        if os.path.exists(os.path.join(project_path, "gradlew")):
            return run_cmd(os.path.join(project_path, "gradlew")+" bootRun", project_path, cb)
        return run_cmd("gradle run", project_path, cb)

    # Node / Fullstack (package.json)
    if "package.json" in files:
        content = open(os.path.join(project_path, "package.json"), "r", encoding="utf-8").read()
        cb("📦 Detected Node project")
        return run_cmd("npm start", project_path, cb)

    cb("❌ Unknown project type for project-runner")
    return None
