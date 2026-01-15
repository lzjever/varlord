# ADR 001: Use Double Underscore for Nested Keys

## Status
Accepted

## Context
Configuration sources (Env, CLI, etc.) use flat key-value pairs. We need a way to represent nested structures (e.g., `db.host`) in a flat namespace.

## Decision
Use **double underscore (`__`)** as the separator for nested keys.

**Examples:**
- `DB__HOST` → `db.host`
- `SERVER__PORT` → `server.port`
- `CACHE__REDIS__HOST` → `cache.redis.host`

## Implementation
```python
def normalize_key(key: str) -> str:
    """
    Applies consistent normalization rules:
    1. Convert to lowercase
    2. Replace double underscores (__) with dots (.)
    3. Preserve single underscores
    """
    key = key.lower()
    key = key.replace("__", ".")
    return key
```

## Reasons

1. **Environment Variable Compatibility**
   - Single underscore (`_`) is commonly used in env vars (e.g., `K8S_POD_NAME`)
   - Double underscore reduces conflicts with existing conventions

2. **Clarity**
   - Double underscore clearly indicates nesting
   - Single underscore typically means word separation

3. **Readability**
   - `DB__HOST` is more readable than `DB.HOST`
   - Dots have special meaning in shells

4. **Industry Convention**
   - Similar to Django's settings pattern (`DATABASE__HOST`)
   - Familiar to Python developers

## Alternatives Considered

### Alternative 1: Single underscore (`_`)
**Pros:**
- Simpler
- More common

**Cons:**
- Ambiguous with word separation (e.g., `K8S_POD_NAME`)
- Harder to distinguish nesting from word separation

**Rejected:** Too much ambiguity

### Alternative 2: Dot (`.`)
**Pros:**
- Natural for nested structures
- Commonly used in config files

**Cons:**
- Dots have special meaning in shells
- Not valid in environment variable names
- Requires quoting: `export DB.HOST=localhost`

**Rejected:** Not shell-friendly

### Alternative 3: Custom separator (e.g., `:`)
**Pros:**
- Flexible
- Can be any character

**Cons:**
- Non-standard
- Harder to remember
- May conflict with existing conventions

**Rejected:** Less intuitive

## Consequences

**Positive:**
- Clear nesting indication
- Compatible with existing env var conventions
- Easy to understand and use

**Negative:**
- Users must remember to use double underscore (not single)
- Slightly more verbose than single underscore

**Mitigation:**
- Clear documentation
- Examples in README
- Validation warnings when mixing separators

## Related Decisions
- [ADR 002: Automatic Model Injection](002-auto-model-injection.md)
- [ADR 003: Priority-based Merging](003-priority-merging.md)

## References
- Django settings: https://docs.djangoproject.com/en/stable/topics/settings/
- Twelve-factor app: https://12factor.net/config
