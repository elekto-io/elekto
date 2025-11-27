/*
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
*/

package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestExtractYAMLHeader(t *testing.T) {
	tests := []struct {
		name    string
		content string
		want    string
		wantErr bool
	}{
		{
			name: "valid YAML header with elekto format",
			content: strings.Repeat("-", 61) + "\n" +
				"name: Test User\n" +
				"ID: testuser\n" +
				"info:\n" +
				"  - employer: Test Corp\n" +
				"  - slack: '@testuser'\n" +
				"---\n" +
				"## Bio content\n",
			want:    "name: Test User\nID: testuser\ninfo:\n  - employer: Test Corp\n  - slack: '@testuser'",
			wantErr: false,
		},
		{
			name: "invalid YAML header with wrong start delimiter",
			content: strings.Repeat("-", 60) + "\n" +
				"name: Test User\n" +
				"---\n",
			want:    "",
			wantErr: true,
		},
		{
			name:    "no YAML header",
			content: "Just some content without header",
			want:    "",
			wantErr: true,
		},
		{
			name: "YAML header with extra spaces",
			content: strings.Repeat("-", 61) + "   \n" +
				"name: Test User\n" +
				"ID: testuser\n" +
				"---  \n" +
				"## Bio content\n",
			want:    "name: Test User\nID: testuser",
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := extractYAMLHeader(tt.content)
			if (err != nil) != tt.wantErr {
				t.Errorf("extractYAMLHeader() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got != tt.want {
				t.Errorf("extractYAMLHeader() = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestCountWords(t *testing.T) {
	tests := []struct {
		name    string
		content string
		want    int
	}{
		{
			name:    "simple sentence",
			content: "Hello world test",
			want:    3,
		},
		{
			name:    "text with newlines",
			content: "Hello\nworld\ntest",
			want:    3,
		},
		{
			name:    "text with multiple spaces",
			content: "Hello    world     test",
			want:    3,
		},
		{
			name:    "empty content",
			content: "",
			want:    0,
		},
		{
			name:    "only whitespace",
			content: "   \n\t  \n  ",
			want:    0,
		},
		{
			name:    "mixed content with punctuation",
			content: "Hello, world! This is a test.",
			want:    6,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a temporary file with the content
			tmpfile, err := os.CreateTemp("", "test")
			if err != nil {
				t.Fatal(err)
			}
			defer os.Remove(tmpfile.Name())

			if _, err := tmpfile.Write([]byte(tt.content)); err != nil {
				t.Fatal(err)
			}
			if err := tmpfile.Close(); err != nil {
				t.Fatal(err)
			}

			got, err := countWords(tmpfile.Name())
			if err != nil {
				t.Errorf("countWords() error = %v", err)
				return
			}
			if got != tt.want {
				t.Errorf("countWords() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestValidateFileNameAndID(t *testing.T) {
	tests := []struct {
		name        string
		filename    string
		fileContent string
		wantErr     bool
		errContains string
	}{
		{
			name:     "valid filename and matching ID",
			filename: "candidate-testuser.md",
			fileContent: strings.Repeat("-", 61) + "\n" +
				"name: Test User\n" +
				"ID: testuser\n" +
				"info:\n" +
				"  - employer: Test Corp\n" +
				"  - slack: '@testuser'\n" +
				"---\n" +
				"## Bio content\n",
			wantErr: false,
		},
		{
			name:        "invalid filename format",
			filename:    "invalid-format.md",
			fileContent: "dummy content",
			wantErr:     true,
			errContains: "filename must follow format",
		},
		{
			name:     "mismatched ID",
			filename: "candidate-testuser.md",
			fileContent: strings.Repeat("-", 61) + "\n" +
				"name: Test User\n" +
				"ID: differentuser\n" +
				"info:\n" +
				"  - employer: Test Corp\n" +
				"---\n" +
				"## Bio content\n",
			wantErr:     true,
			errContains: "does not match ID",
		},
		{
			name:        "missing ID field",
			filename:    "candidate-testuser.md",
			fileContent: strings.Repeat("-", 61) + "\nname: Test User\n---\n",
			wantErr:     true,
			errContains: "missing 'ID' field",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a temporary file with the content
			tmpfile, err := os.CreateTemp("", tt.filename)
			if err != nil {
				t.Fatal(err)
			}
			defer os.Remove(tmpfile.Name())

			// Rename to the desired filename
			dir := filepath.Dir(tmpfile.Name())
			targetPath := filepath.Join(dir, tt.filename)
			if err := os.Rename(tmpfile.Name(), targetPath); err != nil {
				t.Fatal(err)
			}
			defer os.Remove(targetPath)

			if err := os.WriteFile(targetPath, []byte(tt.fileContent), 0644); err != nil {
				t.Fatal(err)
			}

			err = validateFileNameAndID(targetPath)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateFileNameAndID() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.wantErr && tt.errContains != "" && !strings.Contains(err.Error(), tt.errContains) {
				t.Errorf("validateFileNameAndID() error = %v, should contain %q", err, tt.errContains)
			}
		})
	}
}

func TestValidateRequiredFields(t *testing.T) {
	validContent := strings.Repeat("-", 61) + "\n" +
		"name: Test User\n" +
		"ID: testuser\n" +
		"info:\n" +
		"  - employer: Test Corp\n" +
		"  - slack: '@testuser'\n" +
		"---\n" +
		"## Bio content\n"

	tests := []struct {
		name        string
		content     string
		config      *ElectionConfig
		wantErr     bool
		errContains string
	}{
		{
			name:    "valid with no required info fields",
			content: validContent,
			config:  &ElectionConfig{},
			wantErr: false,
		},
		{
			name:    "valid with matching required info fields",
			content: validContent,
			config: &ElectionConfig{
				ShowCandidateFields: []string{"employer", "slack"},
			},
			wantErr: false,
		},
		{
			name: "missing required field - name",
			content: strings.Repeat("-", 61) + "\n" +
				"ID: testuser\n" +
				"info:\n" +
				"  - employer: Test Corp\n" +
				"---\n",
			config:      &ElectionConfig{},
			wantErr:     true,
			errContains: "missing required field: name",
		},
		{
			name: "missing required field - ID",
			content: strings.Repeat("-", 61) + "\n" +
				"name: Test User\n" +
				"info:\n" +
				"  - employer: Test Corp\n" +
				"---\n",
			config:      &ElectionConfig{},
			wantErr:     true,
			errContains: "missing required field: ID",
		},
		{
			name:    "missing required info field",
			content: validContent,
			config: &ElectionConfig{
				ShowCandidateFields: []string{"employer", "slack", "location"},
			},
			wantErr:     true,
			errContains: "missing required info field: location",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a temporary file with the content
			tmpfile, err := os.CreateTemp("", "test")
			if err != nil {
				t.Fatal(err)
			}
			defer os.Remove(tmpfile.Name())

			if err := os.WriteFile(tmpfile.Name(), []byte(tt.content), 0644); err != nil {
				t.Fatal(err)
			}

			err = validateRequiredFields(tmpfile.Name(), tt.config)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateRequiredFields() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.wantErr && tt.errContains != "" && !strings.Contains(err.Error(), tt.errContains) {
				t.Errorf("validateRequiredFields() error = %v, should contain %q", err, tt.errContains)
			}
		})
	}
}

func TestValidateRequiredSections(t *testing.T) {
	validContent := strings.Repeat("-", 61) + "\n" +
		"name: Test User\n" +
		"ID: testuser\n" +
		"---\n" +
		"## About Me\n" +
		"Some content\n" +
		"## Platform\n" +
		"More content\n"

	tests := []struct {
		name        string
		content     string
		sections    []string
		wantErr     bool
		errContains string
	}{
		{
			name:     "all required sections present",
			content:  validContent,
			sections: []string{"## About Me", "## Platform"},
			wantErr:  false,
		},
		{
			name:     "no required sections",
			content:  validContent,
			sections: []string{},
			wantErr:  false,
		},
		{
			name:        "missing required section",
			content:     validContent,
			sections:    []string{"## About Me", "## Platform", "## Experience"},
			wantErr:     true,
			errContains: "missing required section: ## Experience",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a temporary file with the content
			tmpfile, err := os.CreateTemp("", "test")
			if err != nil {
				t.Fatal(err)
			}
			defer os.Remove(tmpfile.Name())

			if err := os.WriteFile(tmpfile.Name(), []byte(tt.content), 0644); err != nil {
				t.Fatal(err)
			}

			err = validateRequiredSections(tmpfile.Name(), tt.sections)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateRequiredSections() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.wantErr && tt.errContains != "" && !strings.Contains(err.Error(), tt.errContains) {
				t.Errorf("validateRequiredSections() error = %v, should contain %q", err, tt.errContains)
			}
		})
	}
}

func TestFindCandidateFiles(t *testing.T) {
	// Create a temporary directory structure
	tmpDir, err := os.MkdirTemp("", "election")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	// Create test files
	testFiles := []struct {
		path       string
		shouldFind bool
	}{
		{filepath.Join(tmpDir, "candidate-user1.md"), true},
		{filepath.Join(tmpDir, "candidate-user2.md"), true},
		{filepath.Join(tmpDir, "not-candidate.md"), false},
		{filepath.Join(tmpDir, "candidate-user3.txt"), false},
		{filepath.Join(tmpDir, "subdir", "candidate-user4.md"), true},
	}

	var expectedFiles []string
	for _, tf := range testFiles {
		dir := filepath.Dir(tf.path)
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(tf.path, []byte("dummy content"), 0644); err != nil {
			t.Fatal(err)
		}
		if tf.shouldFind {
			expectedFiles = append(expectedFiles, tf.path)
		}
	}

	// Test findCandidateFiles
	candidateFiles, err := findCandidateFiles(tmpDir)
	if err != nil {
		t.Errorf("findCandidateFiles() error = %v", err)
		return
	}

	if len(candidateFiles) != len(expectedFiles) {
		t.Errorf("findCandidateFiles() found %d files, expected %d", len(candidateFiles), len(expectedFiles))
	}

	// Check that all expected files are found
	for _, expected := range expectedFiles {
		found := false
		for _, actual := range candidateFiles {
			if actual == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("findCandidateFiles() did not find expected file: %s", expected)
		}
	}
}

func TestLoadElectionConfig(t *testing.T) {
	tests := []struct {
		name               string
		configContent      string
		wantFields         []string
		wantErr            bool
	}{
		{
			name: "valid config with show_candidate_fields",
			configContent: `name: Test Election
start_datetime: 2025-01-01T00:00:00Z
end_datetime: 2025-01-31T23:59:59Z
show_candidate_fields:
  - employer
  - slack
`,
			wantFields: []string{"employer", "slack"},
			wantErr:    false,
		},
		{
			name: "valid config without show_candidate_fields",
			configContent: `name: Test Election
start_datetime: 2025-01-01T00:00:00Z
end_datetime: 2025-01-31T23:59:59Z
`,
			wantFields: nil,
			wantErr:    false,
		},
		{
			name:          "invalid YAML",
			configContent: "invalid: yaml: content:\n  - bad",
			wantErr:       true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a temporary directory
			tmpDir, err := os.MkdirTemp("", "election")
			if err != nil {
				t.Fatal(err)
			}
			defer os.RemoveAll(tmpDir)

			// Write election.yaml
			configPath := filepath.Join(tmpDir, "election.yaml")
			if err := os.WriteFile(configPath, []byte(tt.configContent), 0644); err != nil {
				t.Fatal(err)
			}

			config, err := loadElectionConfig(tmpDir)
			if (err != nil) != tt.wantErr {
				t.Errorf("loadElectionConfig() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				if len(config.ShowCandidateFields) != len(tt.wantFields) {
					t.Errorf("loadElectionConfig() fields = %v, want %v", config.ShowCandidateFields, tt.wantFields)
				}
			}
		})
	}
}
