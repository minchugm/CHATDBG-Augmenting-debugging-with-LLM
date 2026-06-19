# ai_debug_console/runner.py
import os
import subprocess
import xml.etree.ElementTree as ET
from typing import Tuple

def detect_java_project_folder(file_path: str):
    folder = os.path.dirname(file_path) or "."
    # walk upward to find pom.xml/build.gradle optionally
    cur = folder
    for _ in range(6):
        if os.path.exists(os.path.join(cur, "pom.xml")) or os.path.exists(os.path.join(cur, "build.gradle")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return folder

def get_maven_main_class(folder: str):
    pom = os.path.join(folder, "pom.xml")
    if not os.path.exists(pom):
        return None
    try:
        tree = ET.parse(pom)
        root = tree.getroot()
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        # exec plugin
        for plugin in root.findall(".//m:plugin", ns):
            a = plugin.find("m:artifactId", ns)
            if a is not None and "exec-maven-plugin" in (a.text or ""):
                mc = plugin.find(".//m:mainClass", ns)
                if mc is not None and mc.text:
                    return mc.text
    except Exception:
        return None
    return None

def run_subprocess(cmd, cwd=None, shell=False, timeout=None) -> Tuple[str, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=shell, timeout=timeout)
        return proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        return e.stdout or "", f"TimeoutExpired: {e}"
    except FileNotFoundError as e:
        return "", f"Tool not found: {e}"
    except Exception as e:
        return "", str(e)

def run_single_file(file_path: str) -> Tuple[str, str]:
    """
    Run or compile & run a single file.
    Returns (stdout, stderr). stderr empty if success.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == ".py":
        return run_subprocess(["python", file_path])
    if file_ext in (".js", ".jsx"):
        return run_subprocess(["node", file_path])
    if file_ext in (".ts", ".tsx"):
        # requires ts-node
        return run_subprocess(["npx", "ts-node", file_path], shell=False)
    if file_ext == ".c":
        exe = os.path.splitext(file_path)[0]
        out, err = run_subprocess(["gcc", file_path, "-o", exe])
        if err:
            return out, err
        return run_subprocess([exe])
    if file_ext == ".cpp":
        exe = os.path.splitext(file_path)[0]
        out, err = run_subprocess(["g++", file_path, "-o", exe])
        if err:
            return out, err
        return run_subprocess([exe])
    if file_ext == ".java":
        folder = detect_java_project_folder(file_path)
        # if maven project
        if os.path.exists(os.path.join(folder, "pom.xml")):
            o, e = run_subprocess(["mvn", "compile"], cwd=folder)
            if e:
                return o, e
            main = get_maven_main_class(folder)
            if main:
                return run_subprocess(["mvn", "exec:java", f"-Dexec.mainClass={main}"], cwd=folder, shell=False)
        # not maven → compile class files
        out, err = run_subprocess(["javac", file_path], cwd=folder)
        if err:
            return out, err
        # detect package in source to build fully-qualified name
        pkg = None
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("package "):
                        pkg = line.split()[1].rstrip(";")
                        break
        except Exception:
            pass
        cls = os.path.splitext(os.path.basename(file_path))[0]
        fqcn = f"{pkg}.{cls}" if pkg else cls
        return run_subprocess(["java", "-cp", folder, fqcn], cwd=folder)
    return "", f"⚠️ Unsupported file extension: {file_ext}"
