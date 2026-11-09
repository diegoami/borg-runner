"""A model plays Angband from the screen, one key at a time.

The harness here is deliberately thin: it writes the screen, reads keys and
records both. Every judgement about how to play belongs to the model, in the
prompt - see docs/DESIGN.md.
"""
