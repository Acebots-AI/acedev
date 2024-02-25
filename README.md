# Project Name

## Description

This project is designed to seamlessly integrate with GitHub, handling GitHub events and providing an AI-driven interaction model for software engineering tasks. It aims to automate and enhance the software development workflow by leveraging AI capabilities.

## Quickstart Guide

1. Clone the repository: `git clone git@github.com:Acebots-AI/acedev.git`
2. Install Poetry: `pipx install poetry`
3. Install the necessary dependencies: `poetry install`
4. Set up the required environment variables by copying `.env.template` to `.env` and filling in the values.
5. Run the application: `poetry run uvicorn acedev.main:main --host 0.0.0.0 --port 8000`

## Development Guide

- **Setting Up**: Ensure you have Python and Poetry installed and clone the repository. Install dependencies as mentioned in the Quickstart Guide.
- **Project Structure**: The project is structured around the `acedev` directory, with a focus on handling GitHub events and AI-driven interactions.

## API Reference

The `acedev/api/webhook.py` file contains the API for handling GitHub events. This section will be expanded with detailed endpoint documentation, expected payloads, and example responses.

