"""
Configuration for the bioinformatics pipeline launcher skill.
"""

# Cirro platform base URL
CIRRO_BASE_URL = "app.cirro.bio"

# Claude model to use via the Anthropic API
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Model ID for AWS Bedrock
BEDROCK_MODEL = "anthropic.claude-sonnet-4-20250514-v1:0"

# Maximum number of bytes to read when inspecting file contents.
# Keeps tool responses within a reasonable token budget.
MAX_FILE_READ_BYTES = 50_000

# Maximum conversation turns before forcing a summary
MAX_TURNS = 50
