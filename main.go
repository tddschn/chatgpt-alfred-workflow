package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	"github.com/deanishe/awgo"
	"github.com/spf13/pflag"
)

type Config struct {
	PreComputedRowsJSON         string
	MessagePreviewLen           int
	AlfredSubtitleMaxLength     int
	PreComputedAlfredJSON       string
	AlfredWorkflowCacheKey      string
}

type Row struct {
	SearchKey             string `json:"_search_key"`
	ConcatenatedMessages  string `json:"concatenated_messages"`
	MessagePreview        string `json:"_message_preview"`
	Title                 string `json:"_title"`
	QuicklookURL          string `json:"_quicklookurl"`
	ChatGPTURL            string `json:"_chatgpt_url"`
	TypingMindURL         string `json:"_typingmind_url"`
	Item3Kwargs           map[string]interface{} `json:"_item3_kwargs"`
}

var (
	wf *aw.Workflow
	config Config
)

func loadConfig() Config {
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		panic(err)
	}

	config := Config{
		PreComputedRowsJSON:         filepath.Join(dir, "generated/pre_computed_rows.json"),
		MessagePreviewLen:           100,
		AlfredSubtitleMaxLength:     108,
		PreComputedAlfredJSON:       filepath.Join(dir, "generated/pre_computed_alfred.json"),
		AlfredWorkflowCacheKey:      "chatgpt-alfred-workflow",
	}
	return config
}

func loadRows() []Row {
	file, err := ioutil.ReadFile(config.PreComputedRowsJSON)
	if err != nil {
		panic(err)
	}

	var rows []Row
	if err := json.Unmarshal(file, &rows); err != nil {
		panic(err)
	}
	return rows
}

func filterQuery(rows []Row, query string) []Row {
	newRows := []Row{}
	for _, row := range rows {
		longStr := row.SearchKey
		match := true
		for _, subquery := range strings.Split(strings.ToLower(query), "|") {
			if strings.Contains(subquery, "=") {
				parts := strings.SplitN(subquery, "=", 2)
				k, v := parts[0], parts[1]
				if val, ok := row.Item3Kwargs[k]; ok {
					if !strings.Contains(strings.ToLower(fmt.Sprintf("%v", val)), strings.ToLower(v)) {
						match = false
						break
					}
				} else {
					match = false
					break
				}
			} else {
				if !fuzzyMatch(subquery, longStr) {
					match = false
					break
				}
			}
		}
		if match {
			newRows = append(newRows, row)
		}
	}
	return newRows
}

func fuzzyMatch(query, target string) bool {
	query = strings.ToLower(query)
	target = strings.ToLower(target)
	queryIndex := 0

	for i := 0; i < len(target) && queryIndex < len(query); i++ {
		if query[queryIndex] == target[i] {
			queryIndex++
		}
	}
	return queryIndex == len(query)
}

func prepareWfItems(query string, rows []Row) {
	for _, row := range rows {
		messagePreview := row.MessagePreview
		if query != "" {
			messagePreview = searchAndExtractPreview(query, row.ConcatenatedMessages, config.MessagePreviewLen, false)
		}
		item := wf.NewItem(row.Title).
			Subtitle(messagePreview).
			Arg(row.ChatGPTURL).
			Valid(true)

		item.NewModifier("cmd").
			Subtitle("Open on TypingMind").
			Arg(row.TypingMindURL).
			Valid(true)
	}
}

func searchAndExtractPreview(query, message string, returnLen int, caseSensitive bool) string {
	if !caseSensitive {
		query = strings.ToLower(query)
		message = strings.ToLower(message)
	}

	if strings.Contains(message, query) {
		queryIndex := strings.Index(message, query)
		startIndex := max(0, queryIndex-returnLen/2)
		endIndex := min(len(message), queryIndex+len(query)+returnLen/2)

		for endIndex-startIndex < returnLen {
			if startIndex > 0 {
				startIndex--
			} else if endIndex < len(message) {
				endIndex++
			} else {
				break
			}
		}
		return message[startIndex:endIndex]
	}
	return ""
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func run() {
	var generateAlfredJSON bool

	pflag.BoolVarP(&generateAlfredJSON, "generate-alfred-json", "g", false, "Generate Alfred JSON")
	pflag.Parse()

	wf.Args() = pflag.Args()
	config = loadConfig()

	rows := loadRows()

	if generateAlfredJSON {
		prepareWfItems("", rows)
		wf.Run(func() {
			wf.OutputText(wf.Items())
		})
	} else {
		query := ""
		if len(wf.Args()) > 0 {
			query = wf.Args()[0]
		}
		if query != "" {
			rows = filterQuery(rows, query)
		}

		if len(rows) == 0 {
			wf.NewItem("No matching results found")
		} else {
			prepareWfItems(query, rows)
		}
		wf.SendFeedback()
	}
}

func main() {
	wf = aw.New()
	wf.Run(run)
}
