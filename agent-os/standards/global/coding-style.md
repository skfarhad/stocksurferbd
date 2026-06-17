## Coding style best practices

- **Consistent Naming Conventions**: Establish and follow naming conventions for variables, functions, classes, and files across the codebase.
- **Automated Formatting**: Maintain consistent code style (indentation, line breaks, etc.); `black` is the intended formatter.
- **Meaningful Names**: Choose descriptive names that reveal intent; avoid abbreviations and single-letter variables except in narrow contexts.
- **Small, Focused Functions**: Keep functions small and focused on a single task for better readability and testability.
- **Consistent Indentation**: Use 4-space indentation (PEP 8) and configure your editor/linter to enforce it.
- **Remove Dead Code**: Delete unused code, commented-out blocks, and imports rather than leaving them as clutter. Several scrapers carry commented-out debug `print`s and dead branches — prefer removing them.
- **Backward compatibility only when required**: Unless specifically instructed otherwise, assume you do not need to write extra code to preserve backward compatibility.
- **DRY Principle**: Avoid duplication by extracting common logic into reusable functions. For example, the `parse_float` / `parse_int` helpers are duplicated across `PriceData` and `FundamentalData` — shared parsing helpers should live in one place.

## Constants over magic strings

- Source URLs, table CSS classes, and column names are repeated string literals. Keep them as named class-level constants (as `PriceData` already does for its URLs) rather than inline literals, so a site change is a one-line edit.
- Market codes (`'DSE'`, `'CSE'`) and other small closed sets should be defined once and referenced, not retyped at each call site.
