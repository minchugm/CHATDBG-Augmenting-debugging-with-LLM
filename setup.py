from setuptools import setup, find_packages

setup(
    name="ai-debug",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "ai-debug=ai_debug_console.cli:main"
        ]
    },
)
