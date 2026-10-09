// Create a text parameter named DashboardFolder pointing to data/dashboard.
// Create a blank query named DashboardCsv and paste this function in Advanced Editor.
// Then create nine queries with DashboardCsv("dashboard_<name>").
(fileName as text) as table =>
let
    Manifest = Json.Document(File.Contents(DashboardFolder & "\dashboard_manifest.json")),
    Contract = Record.Field(Manifest[tables], fileName),
    Source = Csv.Document(
        File.Contents(DashboardFolder & "\" & fileName & ".csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    ExpectedHeaders = List.Transform(Contract[columns], each _[name]),
    Checked = if Table.ColumnNames(Headers) = ExpectedHeaders then Headers
              else error "CSV headers differ from the validated dashboard manifest",
    Nulls = Table.ReplaceValue(Checked, "", null, Replacer.ReplaceValue, ExpectedHeaders),
    TypePairs = List.Transform(Contract[columns], each {
        _[name],
        if _[powerbi_type] = "Whole number" then Int64.Type
        else if _[powerbi_type] = "Date" then type date
        else type text
    }),
    Typed = Table.TransformColumnTypes(Nulls, TypePairs, "en-US")
in
    Typed
