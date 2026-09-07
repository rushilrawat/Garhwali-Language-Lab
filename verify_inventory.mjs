import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const path = "/Users/rushilrawat/Documents/ChatGPT/Garhwali/outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx";
const blob = await FileBlob.load(path);
const wb = await SpreadsheetFile.importXlsx(blob);

const sheets = await wb.inspect({ kind: "sheet", include: "id,name", maxChars: 3000 });
const summary = await wb.inspect({ kind: "region", sheetId: "Inventory", range: "A5:N8", maxChars: 5000 });
const formulas = await wb.inspect({ kind: "formula", sheetId: "Inventory", range: "A1:Q31", maxChars: 5000, options: { maxResults: 50 } });
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, maxChars: 5000 });

console.log("SHEETS");
console.log(sheets.ndjson ?? String(sheets));
console.log("SUMMARY");
console.log(summary.ndjson ?? String(summary));
console.log("FORMULAS");
console.log(formulas.ndjson ?? String(formulas));
console.log("ERRORS");
console.log(errors.ndjson ?? String(errors));
