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

Adapted from https://github.com/kubernetes/community/blob/master/hack/verify-steering-election-tool.go
*/

package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	yaml "gopkg.in/yaml.v3"
)

type ValidationError struct {
	File    string
	Message string
}

type CandidateHeader struct {
	Name string                 `yaml:"name"`
	ID   string                 `yaml:"ID"`
	Info []map[string]string    `yaml:"info"`
}

type ElectionConfig struct {
	ShowCandidateFields []string `yaml:"show_candidate_fields"`
}

var (
	maxWords          int
	recommendedWords  int
	requiredSections  string
)

func main() {
	flag.IntVar(&maxWords, "max-words", 0, "Maximum word count (0 = no limit)")
	flag.IntVar(&recommendedWords, "recommended-words", 0, "Recommended word count (shown in error messages)")
	flag.StringVar(&requiredSections, "required-sections", "", "Comma-separated list of required section headers")
	flag.Parse()

	if flag.NArg() < 1 {
		fmt.Fprintf(os.Stderr, "Usage: %s [flags] <election-path>\n", os.Args[0])
		flag.PrintDefaults()
		os.Exit(1)
	}

	electionPath := flag.Arg(0)

	// Load election configuration
	config, err := loadElectionConfig(electionPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Could not load election.yaml: %v\n", err)
		config = &ElectionConfig{} // Continue with empty config
	}

	// Find candidate files
	candidateFiles, err := findCandidateFiles(electionPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error finding candidate files: %v\n", err)
		os.Exit(1)
	}

	if len(candidateFiles) == 0 {
		fmt.Fprintf(os.Stderr, "No candidate files found in %s\n", electionPath)
		os.Exit(1)
	}

	// Parse required sections
	var sections []string
	if requiredSections != "" {
		sections = strings.Split(requiredSections, ",")
		for i := range sections {
			sections[i] = strings.TrimSpace(sections[i])
		}
	}

	var errors []ValidationError

	for _, candidateFile := range candidateFiles {
		// Check word count
		if maxWords > 0 {
			wordCount, err := countWords(candidateFile)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error counting words in %s: %v\n", candidateFile, err)
				continue
			}

			if wordCount > maxWords {
				errors = append(errors, ValidationError{
					File:    candidateFile,
					Message: fmt.Sprintf("has %d words", wordCount),
				})
			}
		}

		// Check filename format and GitHub ID matching
		if err := validateFileNameAndID(candidateFile); err != nil {
			errors = append(errors, ValidationError{
				File:    candidateFile,
				Message: err.Error(),
			})
		}

		// Check required fields
		if err := validateRequiredFields(candidateFile, config); err != nil {
			errors = append(errors, ValidationError{
				File:    candidateFile,
				Message: err.Error(),
			})
		}

		// Check required sections
		if len(sections) > 0 {
			if err := validateRequiredSections(candidateFile, sections); err != nil {
				errors = append(errors, ValidationError{
					File:    candidateFile,
					Message: err.Error(),
				})
			}
		}
	}

	if len(errors) > 0 {
		for _, err := range errors {
			fmt.Printf("%s: %s\n", err.File, err.Message)
		}

		separator := strings.Repeat("=", 68)
		fmt.Printf("\n%s\n", separator)
		fmt.Printf("%d invalid candidate bio(s) detected.\n", len(errors))
		if recommendedWords > 0 {
			fmt.Printf("Bios should be limited to around %d words, excluding headers.\n", recommendedWords)
		}
		fmt.Printf("Bios must follow the nomination template and filename format.\n")
		fmt.Printf("%s\n", separator)
		os.Exit(1)
	}

	fmt.Printf("All %d candidate bio(s) validated successfully.\n", len(candidateFiles))
}

// findCandidateFiles finds all candidate bio files in the election directory
func findCandidateFiles(electionPath string) ([]string, error) {
	var candidateFiles []string

	err := filepath.Walk(electionPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip if not a regular file
		if !info.Mode().IsRegular() {
			return nil
		}

		// Check if it's a candidate bio file
		if strings.HasPrefix(info.Name(), "candidate-") && strings.HasSuffix(info.Name(), ".md") {
			candidateFiles = append(candidateFiles, path)
		}

		return nil
	})

	return candidateFiles, err
}

// loadElectionConfig loads the election configuration from election.yaml
func loadElectionConfig(electionPath string) (*ElectionConfig, error) {
	configPath := filepath.Join(electionPath, "election.yaml")
	content, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var config ElectionConfig
	if err := yaml.Unmarshal(content, &config); err != nil {
		return nil, err
	}

	return &config, nil
}

// countWords counts the number of words in a file
func countWords(filename string) (int, error) {
	content, err := os.ReadFile(filename)
	if err != nil {
		return 0, err
	}

	// Split by whitespace and count non-empty strings
	words := regexp.MustCompile(`\s+`).Split(string(content), -1)
	count := 0
	for _, word := range words {
		if strings.TrimSpace(word) != "" {
			count++
		}
	}

	return count, nil
}

// validateFileNameAndID checks if filename matches format candidate-$username.md
// and if the username matches the ID in the document header
func validateFileNameAndID(filename string) error {
	// Extract filename from path
	base := filepath.Base(filename)

	// Check filename format: candidate-*.md
	candidateRegex := regexp.MustCompile(`^candidate-([a-zA-Z0-9_-]+)\.md$`)
	matches := candidateRegex.FindStringSubmatch(base)
	if len(matches) != 2 {
		return fmt.Errorf("filename must follow format 'candidate-username.md'")
	}

	expectedUsername := matches[1]

	// Read file content to extract ID
	content, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("error reading file: %v", err)
	}

	// Extract YAML header and parse it
	yamlHeader, err := extractYAMLHeader(string(content))
	if err != nil {
		return fmt.Errorf("error extracting YAML header: %v", err)
	}

	// Parse the YAML to get the ID field
	var header map[string]interface{}
	if err := yaml.Unmarshal([]byte(yamlHeader), &header); err != nil {
		return fmt.Errorf("error parsing YAML header: %v", err)
	}

	idValue, exists := header["ID"]
	if !exists {
		return fmt.Errorf("missing 'ID' field in header")
	}

	actualUsername, ok := idValue.(string)
	if !ok {
		return fmt.Errorf("'ID' field must be a string")
	}

	actualUsername = strings.TrimSpace(actualUsername)
	if actualUsername != expectedUsername {
		return fmt.Errorf("filename username '%s' does not match ID '%s' in header", expectedUsername, actualUsername)
	}

	return nil
}

// validateRequiredFields checks that required YAML fields are present
func validateRequiredFields(filename string, config *ElectionConfig) error {
	content, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("error reading file: %v", err)
	}

	contentStr := string(content)

	// Extract YAML header
	yamlHeader, err := extractYAMLHeader(contentStr)
	if err != nil {
		return fmt.Errorf("error extracting YAML header: %v", err)
	}

	// Parse YAML header
	var header CandidateHeader
	if err := yaml.Unmarshal([]byte(yamlHeader), &header); err != nil {
		return fmt.Errorf("invalid YAML header format: %v", err)
	}

	// Validate required fields
	if header.Name == "" {
		return fmt.Errorf("missing required field: name")
	}
	if header.ID == "" {
		return fmt.Errorf("missing required field: ID")
	}

	// Validate info fields if show_candidate_fields is set
	if len(config.ShowCandidateFields) > 0 {
		// Build a map of available info fields
		infoFields := make(map[string]bool)
		for _, infoItem := range header.Info {
			for key := range infoItem {
				infoFields[key] = true
			}
		}

		// Check each required field
		for _, requiredField := range config.ShowCandidateFields {
			if !infoFields[requiredField] {
				return fmt.Errorf("missing required info field: %s", requiredField)
			}
		}
	}

	return nil
}

// validateRequiredSections checks that required markdown sections are present
func validateRequiredSections(filename string, sections []string) error {
	content, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("error reading file: %v", err)
	}

	contentStr := string(content)

	for _, section := range sections {
		if !strings.Contains(contentStr, section) {
			return fmt.Errorf("missing required section: %s", section)
		}
	}

	return nil
}

// extractYAMLHeader extracts the YAML content between dash separators
// Elekto format: 61 dashes at start, --- at end
func extractYAMLHeader(content string) (string, error) {
	// Find the YAML header between 61 dashes and ---
	dashRegex := regexp.MustCompile(`(?s)^-{61}\s*\n(.*?)\n---\s*\n`)
	matches := dashRegex.FindStringSubmatch(content)
	if len(matches) != 2 {
		return "", fmt.Errorf("could not find YAML header between dashes")
	}
	return matches[1], nil
}
