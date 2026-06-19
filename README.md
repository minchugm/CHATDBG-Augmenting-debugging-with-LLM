# CHATDBG – Augmenting Debugging with LLM

## Overview

CHATDBG is an AI-powered debugging assistant that helps developers identify, analyze, and resolve errors in software projects. The system combines traditional compilation/runtime error detection with Large Language Models (LLMs) to provide intelligent debugging suggestions and explanations.

The tool supports both single-file debugging and project-level debugging for Java and Python applications, enabling developers to quickly locate issues and understand potential fixes.

---

## Features

### AI-Assisted Debugging

* Analyzes compilation and runtime errors.
* Generates human-readable explanations for failures.
* Suggests possible fixes using LLMs.

### Single File Debugging

* Debug individual Java or Python files.
* Detect syntax and execution issues.
* Provide contextual suggestions.

### Project-Level Analysis

* Scan entire project directories.
* Detect multiple source files automatically.
* Compile and execute Java projects.
* Aggregate debugging information.

### Delta Minimization

* Reduce failing input cases to minimal reproducible examples.
* Simplify debugging workflows.

### Cross-Language Support

* Java Projects
* Python Projects

### Command-Line Interface

Simple and lightweight CLI for developers.

---

## Architecture

```text
User
 │
 ▼
CLI Interface (ai-debug)
 │
 ▼
Project/File Analyzer
 │
 ├── Compilation
 ├── Execution
 └── Error Collection
 │
 ▼
LLM Debug Engine
 │
 ▼
Root Cause Analysis
 │
 ▼
Suggested Fixes & Explanations
```

---

## Technology Stack

### Programming Languages

* Python
* Java

### Libraries & Frameworks

* Google Gemini API
* argparse
* setuptools

### Development Tools

* Git
* GitHub
* VS Code

---

## Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/CHATDBG-Augmenting-debugging-with-LLM.git
cd CHATDBG-Augmenting-debugging-with-LLM
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -e .
```

---

## Configuration

Create a configuration file:

```json
{
  "google_api_key": "YOUR_API_KEY_HERE",
  "model": "gemini-2.5-flash"
}
```

Store API keys securely and do not commit them to GitHub.

---

## Usage

### Debug a Single File

```bash
ai-debug debug --file Hello.java
```

### Debug a Python File

```bash
ai-debug debug --file app.py
```

### Debug an Entire Project

```bash
ai-debug debug --project Sample_code
```

### Offline Mode

```bash
ai-debug debug --project Sample_code --offline
```

---

## Sample Workflow

1. User selects a file or project.
2. CHATDBG compiles and executes the code.
3. Errors are collected automatically.
4. LLM analyzes the failure.
5. Suggested fixes are generated.
6. Developer applies corrections.

---

## Project Structure

```text
CHATDBG-Augmenting-debugging-with-LLM/
│
├── ai_debug_console/
│   ├── cli.py
│   ├── debug.py
│   ├── project.py
│   ├── project_runner.py
│   ├── runner.py
│   ├── server.py
│   └── utils.py
│
├── Sample_code/
│
├── package.json
├── package-lock.json
├── pyproject.toml
├── setup.py
├── ai-debug.cmd
├── README.md
└── .gitignore
```

---

## Future Enhancements

* Web-based dashboard
* VS Code extension
* Multi-language support
* Automated bug fixing
* Test case generation
* CI/CD integration
* Docker support

---

## Learning Outcomes

* Large Language Model Integration
* Software Debugging Automation
* Python Package Development
* Java Project Compilation
* Command Line Application Design
* Git & GitHub Version Control

---

## Author

**Minchu G M**

Final Year Engineering Student

Project: CHATDBG – Augmenting Debugging with LLM

---

## License

This project is intended for educational and research purposes.
