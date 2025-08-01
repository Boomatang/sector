# Sector

Sector is a CLI tool designed to aid in the release process of Kuadrant projects. It provides an easy way to analyze project release dependencies, track what's new between releases, and get detailed breakdowns of dependency chains across the Kuadrant ecosystem.

## Features

- **Release Analysis**: Get detailed information about project releases, including commits and PRs
- **Dependency Tracking**: Parse and visualize dependency chains from `release.yaml` files
- **Multi-Project Support**: Analyze multiple related projects simultaneously
- **GitHub Integration**: Fetch real-time data from GitHub releases, commits, and pull requests
- **Flexible Sorting**: Sort results by time or project name
- **Rich Output**: Beautiful terminal output with trees and formatted data

## Requirements

- Python 3.10 or higher
- GitHub Personal Access Token (set as `GITHUB_TOKEN` environment variable)

## Installation

### Using pipx (Recommended)

```sh
pipx install git+https://github.com/Boomatang/sector.git
```

### Using pip

```sh
pip install git+https://github.com/Boomatang/sector.git
```

### Development Installation

```sh
git clone https://github.com/Boomatang/sector.git
cd sector
poetry install
```

## Setup

Before using Sector, you need to set up a GitHub Personal Access Token:

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Create a new token with `repo` access
3. Export it as an environment variable:

```sh
export GITHUB_TOKEN="your_token_here"
```

## Usage

Sector provides two main commands:

### `future` - Analyze Multiple Projects

Get information about multiple projects and what's coming in future releases:

```sh
# Basic usage - analyze default Kuadrant projects
sector future

# Analyze specific projects
sector future -p authorino -p limitador

# Get detailed information (slower, more API calls)
sector future --detailed

# Analyze specific version/tag
sector future -p "kuadrant-operator@v0.5.0" --detailed

# Sort by name instead of time
sector future --sort name
```

### `current` - Analyze Release Dependencies

Get a breakdown of the current released version and its entire dependency chain:

```sh
# Analyze latest kuadrant-operator release
sector current

# Analyze specific project
sector current -p dns-operator

# Analyze specific version
sector current --version v0.5.0

# Use custom configuration file
sector current -c ./my-config.toml
```

## Command Options

### Global Options

- `--debug`: Enable debug logging
- `--help`: Show help message

### `future` Command Options

- `--owner`: GitHub organization/owner (default: kuadrant)
- `-p, --project`: Project to analyze (can be used multiple times)
- `--sort`: Sort order - `time` or `name` (default: time)
- `--detailed`: Show detailed PR and commit information

### `current` Command Options

- `--owner`: GitHub organization/owner (default: kuadrant)
- `-p, --project`: Main project to analyze (default: kuadrant-operator)
- `-c, --configuration-file`: Path to configuration file (default: ./config.toml)
- `--sort`: Sort order - `time` or `name` (default: time)  
- `--version`: Version to analyze (default: latest)

## Configuration

The `current` command can use a TOML configuration file for mapping project names. Example `config.toml`:

```toml
[mapper]
old-name = "new-name"
internal-name = "public-name"
```

## Project Format

Projects can be specified in the following formats:
- `project-name` - Uses latest release
- `project-name@tag` - Uses specific tag/version
- `project-name@main` - Uses main branch

## Default Projects

The `future` command analyzes these Kuadrant projects by default:
- authorino
- authorino-operator  
- dns-operator
- kuadrant-console-plugin
- kuadrantctl
- kuadrant-operator
- limitador
- limitador-operator
- wasm-shim

## Examples

```sh
# See what's new across all Kuadrant projects
sector future --detailed

# Analyze the dependency tree for latest kuadrant-operator
sector current

# Compare a specific release to main
sector future -p "kuadrant-operator@v0.5.0" --detailed

# Get current state of a specific version
sector current --version v0.4.0
```

## Development

This project uses Poetry for dependency management:

```sh
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Type checking
poetry run mypy src/
```

## License

This project is licensed under the MIT License.
