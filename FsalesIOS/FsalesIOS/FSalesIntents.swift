import AppIntents

struct OpenQuotationIntent: AppIntent {
    static var title: LocalizedStringResource = "Open FSales quotations"
    static var description = IntentDescription("Open the quotation workflow in FSales.")
    static var openAppWhenRun = true

    func perform() async throws -> some IntentResult {
        .result()
    }
}

struct FSalesShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: OpenQuotationIntent(),
            phrases: [
                "Open quotations in \(.applicationName)",
                "Create a quotation in \(.applicationName)"
            ],
            shortTitle: "Open Quotations",
            systemImageName: "doc.text"
        )
    }
}
