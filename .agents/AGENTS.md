
- **Localization**: NEVER hardcode user-facing strings in Python or UI files. Always link them to the language files (e.g. `tr("...")`) and add the corresponding translation keys to both `en.json` and `tr.json`.
- **Documentation**: ALWAYS update the project documentation (README.md, DEVELOPMENT_SUMMARY.md, architecture docs, etc.) whenever you make codebase changes. Do this systematically after completing any feature or fix.
