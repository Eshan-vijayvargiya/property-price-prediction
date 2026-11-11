// Power Query (Excel): pulls every sign-in from the Google Sheet into a table that refreshes.
// Paste into Excel: Data -> Get Data -> From Other Sources -> Blank Query -> Advanced Editor.
// Replace the two values below with your web-app URL (ends in /exec) and the KEY from your Apps Script.
let
    Url = "https://script.google.com/macros/s/PASTE-YOUR-DEPLOYMENT-ID/exec",
    Key = "change-me-to-a-long-secret-word",
    Source = Json.Document(Web.Contents(Url, [Query = [key = Key]])),
    Checked = if Source is record
        then error Error.Record("The sheet refused", Record.FieldOrDefault(Source, "error", "check the URL and KEY"))
        else Source,
    Rows = Table.FromRecords(Checked, {"time", "name", "mobile", "email", "app"}, MissingField.UseNull),
    Times = Table.TransformColumns(Rows, {{"time", each try DateTimeZone.RemoveZone(DateTimeZone.ToLocal(DateTimeZone.FromText(_))) otherwise null, type datetime}}),
    Typed = Table.TransformColumnTypes(Times, {{"name", type text}, {"mobile", type text}, {"email", type text}, {"app", type text}}),
    Renamed = Table.RenameColumns(Typed, {{"time", "Signed in"}, {"name", "Name"}, {"mobile", "Mobile"}, {"email", "Email"}, {"app", "App"}}),
    Newest = Table.Sort(Renamed, {{"Signed in", Order.Descending}})
in
    Newest
