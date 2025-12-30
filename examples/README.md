# Varlord Examples

This directory contains example scripts demonstrating various features of Varlord.

## Examples

### basic_example.py
Basic usage example showing how to load configuration from defaults, environment variables, and CLI arguments.

Run:
```bash
python examples/basic_example.py
```

With environment variables:
```bash
APP_HOST=0.0.0.0 APP_PORT=9000 python examples/basic_example.py
```

With CLI arguments:
```bash
python examples/basic_example.py --host 0.0.0.0 --port 9000 --debug
```

### priority_example.py
Demonstrates three ways to customize configuration priority:
1. Reordering sources
2. Using priority list
3. Using PriorityPolicy for per-key rules

Run:
```bash
python examples/priority_example.py
```

