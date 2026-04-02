# Getting Started with vcsx

## What is vcsx?

vcsx (Vibe Coding Setup Expert) is a CLI tool that generates **production-ready AI coding environments** in seconds. It supports 8+ AI coding tools and creates skills, hooks, agents, and project scaffolding automatically.

## Installation

### Method 1: PyPI (Recommended)
```bash
pip install vcsx
vcsx init
```

### Method 2: Standalone Executable
```bash
# Download from GitHub Releases
curl -L https://github.com/vibe-coding-setup-expert/vcsx/releases/latest/download/vcsx.exe -o vcsx.exe
./vcsx.exe init
```

### Method 3: Homebrew
```bash
brew tap vcsx/tap
brew install vcsx
```

### Method 4: npx
```bash
npx vcsx init
```

### Method 5: npm
```bash
npm install -g vcsx
vcsx init
```

## Quick Start

```bash
# Start interactive wizard
vcsx init

# Generate for specific AI tools
vcsx init --cli claude-code --cli cursor

# Generate in specific directory
vcsx init -o ./my-project
```

## Available Commands

| Command | Description |
|---------|-------------|
| `vcsx init` | Start interactive setup wizard |
| `vcsx list` | List all supported AI tools |
| `vcsx info <tool>` | Show tool details |
| `vcsx install <method>` | Show install instructions |
| `vcsx doctor` | Check installation health |
| `vcsx plugins` | List installed plugins |
| `vcsx templates` | List available templates |
| `vcsx templates:install <name>` | Install a template |

## Next Steps

- [Configuration Guide](configuration.md)
- [Supported AI Tools](ai-tools.md)
- [Skills Reference](skills.md)
- [Hooks Reference](hooks.md)
- [Template System](templates.md)
