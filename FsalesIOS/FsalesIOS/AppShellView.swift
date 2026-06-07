import SwiftUI

enum AppRoute: Hashable {
    case leadDetail(Lead.ID)
    case quotationDetail(Quotation.ID)
}

enum SalesSheet: Identifiable, Hashable {
    case leadEditor(Lead.ID?)
    case quotationEditor(Lead.ID)

    var id: String {
        switch self {
        case .leadEditor(let id): "lead-editor-\(id?.uuidString ?? "new")"
        case .quotationEditor(let id): "quotation-editor-\(id.uuidString)"
        }
    }
}

@MainActor
@Observable
final class SalesRouter {
    var path: [AppRoute] = []
    var presentedSheet: SalesSheet?

    func navigate(to route: AppRoute) {
        path.append(route)
    }
}

struct AppShellView: View {
    @State private var router = SalesRouter()

    var body: some View {
        TabView {
            NavigationStack(path: $router.path) {
                LeadListView()
                    .withSalesDestinations()
            }
            .environment(router)
            .withSalesSheets(sheet: $router.presentedSheet)
            .tabItem {
                Label("Leads", systemImage: "person.2")
            }

            NavigationStack(path: $router.path) {
                QuotationListView()
                    .withSalesDestinations()
            }
            .environment(router)
            .withSalesSheets(sheet: $router.presentedSheet)
            .tabItem {
                Label("Báo giá", systemImage: "doc.text")
            }
        }
    }
}

private extension View {
    func withSalesDestinations() -> some View {
        navigationDestination(for: AppRoute.self) { route in
            switch route {
            case .leadDetail(let id):
                LeadDetailView(leadID: id)
            case .quotationDetail(let id):
                QuotationDetailView(quotationID: id)
            }
        }
    }

    func withSalesSheets(sheet: Binding<SalesSheet?>) -> some View {
        self.sheet(item: sheet) { destination in
            NavigationStack {
                switch destination {
                case .leadEditor(let leadID):
                    LeadEditorView(leadID: leadID)
                case .quotationEditor(let leadID):
                    QuotationEditorView(leadID: leadID)
                }
            }
        }
    }
}
