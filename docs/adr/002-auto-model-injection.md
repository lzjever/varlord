# ADR 002: Automatic Model Injection into Sources

## Status
Accepted

## Context
Configuration sources need to know which fields to load based on the model. Other libraries require passing the model to each source explicitly, which is verbose and error-prone.

## Decision
**Automatically inject the model into all sources** when they are added to a `Config` instance.

**Before (verbose):**
```python
cfg = Config(
    model=AppConfig,
    sources=[
        Env(model=AppConfig),      # Repeat model
        DotEnv(model=AppConfig, path=".env"),  # Repeat model
        Etcd(model=AppConfig, prefix="/app"),  # Repeat model
    ]
)
```

**After (automatic):**
```python
cfg = Config(
    model=AppConfig,
    sources=[
        Env(),      # Model injected automatically
        DotEnv(path=".env"),  # Model injected automatically
        Etcd(prefix="/app"),  # Model injected automatically
    ]
)
```

## Implementation
```python
class Config:
    def __init__(self, model: type, sources: list[Source]):
        self._model = model
        self._sources = []

        for source in sources:
            # Auto-inject model if not already set
            if source._model is None:
                source._model = model
            self._sources.append(source)
```

## Reasons

1. **Reduced Boilerplate**
   - Less repetition
   - Cleaner code
   - Easier to read

2. **Less Error-Prone**
   - Can't forget to pass model to a source
   - All sources guaranteed to have the same model
   - Consistent filtering behavior

3. **Easier Refactoring**
   - Change model in one place
   - Add/remove sources without updating model
   - Sources are reusable across different configs

4. **Backward Compatibility**
   - Sources can still override model if needed
   - Existing code continues to work

## Alternatives Considered

### Alternative 1: Explicit Model Passing (Current Pattern)
**Pros:**
- More explicit
- Clear what model each source uses

**Cons:**
- Verbose
- Error-prone (can forget to pass model)
- Repetitive

**Rejected:** Too much boilerplate

### Alternative 2: Global Model Context
```python
with ConfigContext(model=AppConfig):
    source = Env()  # Uses context model
```

**Pros:**
- Explicit scoping
- Can have different models in different contexts

**Cons:**
- More complex
- Requires context manager
- Not thread-safe by default

**Rejected:** Over-engineering for this use case

### Alternative 3: Model Registry
```python
register_model("default", AppConfig)
source = Env()  # Looks up registered model
```

**Pros:**
- Can have named models
- Can share models across configs

**Cons:**
- Global state
- Not explicit in code
- Magic behavior

**Rejected:** Global state is problematic

## Consequences

**Positive:**
- Cleaner, more maintainable code
- Fewer errors
- Better developer experience

**Negative:**
- Less explicit (model comes from Config)
- Slightly more magic

**Mitigation:**
- Clear documentation
- Source code is easy to understand
- Can still override model if needed

## Usage Patterns

### Basic Usage (Recommended)
```python
cfg = Config(
    model=AppConfig,
    sources=[
        Env(),
        DotEnv(),
        CLI(),
    ]
)
# All sources automatically get AppConfig model
```

### Advanced Usage (Override Model)
```python
# Source with different model
source = CustomSource(model=CustomModel)

# Config still injects into other sources
cfg = Config(
    model=AppConfig,
    sources=[
        Env(),  # Gets AppConfig
        source,  # Keeps CustomModel (already set)
    ]
)
```

## Related Decisions
- [ADR 001: Double Underscore Separator](001-double-underscore-separator.md)
- [ADR 003: Priority-based Merging](003-priority-merging.md)

## References
- Python dependency injection patterns
- Model-View-Controller (MVC) pattern
