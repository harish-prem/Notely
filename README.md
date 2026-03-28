# Notely

To use and help develop this program, install [`uv`](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).

## Usage
### Run directly from GitHub

Run following command in your terminal:

```
uvx https://github.com/harish-prem/Notely/releases/download/test/notely-0.1.0-py3-none-any.whl server start
```

Once the server is up and running, go to http://localhost:2626.

### Run after cloning

Clone this repository and run the following command inside the repo:

```
uv run notely server start
```

## Development

Clone this repository and run the following commands inside the repo:

```
uv venv
./.venv/Scripts/activate
uv sync --all-groups
```
