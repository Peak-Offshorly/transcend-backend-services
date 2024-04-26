# Peak Transcend - Backend Services

## Requirements

- Python 3.10
- PostgreSQL

### Local Setup

Ensure you have `Python v3.10` installed. PyEnv is highly recommended for efficient management of Python versions. The `.python-version` file included in this repository specifies the local version of Python to be used when running the code locally.

Go to `https://github.com/pyenv/pyenv` to follow on how to install pyenv on your system.

### Running locally

Copy `.env.sample` file to `.env` file and update the environment variables

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
