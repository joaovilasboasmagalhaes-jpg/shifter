# Shifter

## Import Date Rule (Current)

When importing dates from spreadsheets:

- Date values are read from the configured spreadsheet axis.
- Each imported date value is currently expected to be an integer day-of-month.
- `import.year` and `import.month` must be present in `config.json` so the importer can build full dates.

Worker names are read from the configured worker axis, and shift cells are read as a matrix starting after the configured date row and worker column.

`import.shift_types` can be used to override the short labels used in the spreadsheet.

Example config:

```json
{
	"import": {
		"date": { "row": true, "index": 2, "header": true },
		"worker": { "row": false, "index": 2, "header": true },
		"year": 2026,
		"month": 2,
		"shift_types": {
			"morning": "M",
			"afternoon": "T",
			"night": "N",
			"vacation": "FE",
			"day_off": "F"
		}
	}
}
```

## Constraints

Hard constraints currently include:

- Five Consecutive Shifts
- Rest Gap

Soft constraints are score-based penalties. Lower score is better.

- Monthly Weekend Off: each working weekend adds a penalty of `1.0`.
