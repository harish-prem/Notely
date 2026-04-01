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
uv run poe setup
```

### Building
#### Executable

To build an executable, ensure you have one of the [supported compilers](https://github.com/Nuitka/Nuitka?tab=readme-ov-file#c-compiler):

Then run the following command:

```
uv run poe build
```

#### Wheel

To build a wheel for use with the `uvx` command in the `Run directly from GitHub` section, run the following command:

```
uv build
```

### Clean

To remove all temporary files, run the following command:

```
uv run poe clean
```