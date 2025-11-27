# Candidate Bio Validator

A Go-based validation tool for Elekto candidate bio files. This tool validates candidate bios against the Elekto format specification and configurable validation rules.

## Overview

Adapted from the [Kubernetes community's verify-steering-election-tool.go](https://github.com/kubernetes/community/blob/master/hack/verify-steering-election-tool.go), this generic validator checks candidate bio files for:

- Correct YAML frontmatter format
- Required fields (name, ID, and election-specific info fields)
- Filename/ID matching
- Optional word count limits
- Optional required markdown sections

## Installation

No installation required! Run directly from GitHub:

```bash
go run github.com/elekto-io/elekto/scripts/validate-bios@latest <election-path>
```

Or for local development, build from source:

```bash
cd scripts/validate-bios
go build -o validate-bios .
```

## Usage

### Basic Validation

```bash
# Run directly from GitHub (recommended)
go run github.com/elekto-io/elekto/scripts/validate-bios@latest /path/to/election

# Or for local development
cd scripts/validate-bios
go run . /path/to/election

# Or with a built binary
cd scripts/validate-bios
./validate-bios /path/to/election
```

### With Options

```bash
# Enforce word limits
go run github.com/elekto-io/elekto/scripts/validate-bios@latest \
  --max-words=450 \
  --recommended-words=300 \
  /path/to/election

# Require specific markdown sections
go run github.com/elekto-io/elekto/scripts/validate-bios@latest \
  --required-sections="## About Me,## Platform,## Why I'm Running" \
  /path/to/election

# Combine all options
go run github.com/elekto-io/elekto/scripts/validate-bios@latest \
  --max-words=450 \
  --recommended-words=300 \
  --required-sections="## About Me,## Platform" \
  /path/to/election
```

## Command-Line Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--max-words` | int | 0 (no limit) | Maximum word count allowed in bio files |
| `--recommended-words` | int | 0 (no limit) | Recommended word count (shown in error messages) |
| `--required-sections` | string | "" | Comma-separated list of required markdown section headers |

## Candidate File Format

Candidate bios must follow the Elekto format:

```markdown
-------------------------------------------------------------
name: Candidate Full Name
ID: github-username
info:
  - employer: Company Name
  - slack: '@username'
-------------------------------------------------------------

## About Me

Bio content here...

## Platform

Platform content here...
```

### Format Specification

- **Start delimiter**: Exactly 61 dashes (`-`)
- **End delimiter**: Three dashes (`---`)
- **Required fields**:
  - `name`: Candidate's full name
  - `ID`: GitHub username (must match filename)
- **Filename format**: `candidate-{ID}.md` where `{ID}` matches the `ID` field in the YAML header
- **Info fields**: List of key-value pairs. Required fields are determined by `show_candidate_fields` in `election.yaml`

## Election Configuration Integration

The validator reads `election.yaml` from the election directory to determine which info fields are required:

```yaml
# election.yaml
name: 2025 Steering Committee Election
start_datetime: 2025-01-01T00:00:00Z
end_datetime: 2025-01-31T23:59:59Z
show_candidate_fields:
  - employer
  - slack
```

If `show_candidate_fields` is specified, the validator will check that each candidate's `info` section contains all listed fields.

## Validation Rules

1. **YAML Header Parsing**
   - Extract YAML between 61-dash start delimiter and `---` end delimiter
   - Validate `name` and `ID` fields exist

2. **Filename/ID Matching**
   - Filename must be `candidate-{ID}.md`
   - ID in filename must match `ID` field in YAML header

3. **Info Fields** (if `show_candidate_fields` is set in `election.yaml`)
   - Validate each listed field exists in the candidate's `info` section

4. **Word Count** (if `--max-words` flag is provided)
   - Count all words in the file
   - Error if count exceeds `--max-words`

5. **Required Sections** (if `--required-sections` flag is provided)
   - Check that bio content contains each specified section header

## Exit Codes

- `0` - All candidate bios validated successfully
- `1` - One or more validation errors detected

## Testing

Run the test suite:

```bash
cd scripts/validate-bios
go test -v
```

## Example Output

### Successful Validation

```
All 5 candidate bio(s) validated successfully.
```

### Failed Validation

```
/path/to/election/candidate-user1.md: has 475 words
/path/to/election/candidate-user2.md: missing required info field: employer
/path/to/election/candidate-user3.md: filename username 'user3' does not match ID 'user-3' in header

====================================================================
3 invalid candidate bio(s) detected.
Bios should be limited to around 300 words, excluding headers.
Bios must follow the nomination template and filename format.
====================================================================
```

## License

Copyright 2025 The Elekto Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Source

Adapted from [kubernetes/community verify-steering-election-tool.go](https://github.com/kubernetes/community/blob/master/hack/verify-steering-election-tool.go)
