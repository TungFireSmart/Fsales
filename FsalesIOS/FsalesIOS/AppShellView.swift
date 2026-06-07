import SwiftUI

enum AppRoute: Hashable {
    case leadDetail(Lead.ID)
    case quotationDetail(Quotation.ID)
    case productDetail(Product.ID)
}

enum SalesSheet: Identifiable, Hashable {
    case leadEditor(Lead.ID?)
    case quotationEditor(Lead.ID)
    case productEditor(Product.ID?)

    var id: String {
        switch self {
        case .leadEditor(let id): "lead-editor-\(id?.uuidString ?? "new")"
        case .quotationEditor(let id): "quotation-editor-\(id.uuidString)"
        case .productEditor(let id): "product-editor-\(id?.uuidString ?? "new")"
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
    @State private var dashboardRouter = SalesRouter()
    @State private var leadRouter = SalesRouter()
    @State private var quotationRouter = SalesRouter()
    @State private var productRouter = SalesRouter()

    var body: some View {
        TabView {
            NavigationStack(path: $dashboardRouter.path) {
                DashboardView()
                    .withSalesDestinations()
            }
            .environment(dashboardRouter)
            .withSalesSheets(sheet: $dashboardRouter.presentedSheet)
            .tabItem {
                Label("Tổng quan", systemImage: "chart.bar")
            }

            NavigationStack(path: $leadRouter.path) {
                LeadListView()
                    .withSalesDestinations()
            }
            .environment(leadRouter)
            .withSalesSheets(sheet: $leadRouter.presentedSheet)
            .tabItem {
                Label("Leads", systemImage: "person.2")
            }

            NavigationStack(path: $quotationRouter.path) {
                QuotationListView()
                    .withSalesDestinations()
            }
            .environment(quotationRouter)
            .withSalesSheets(sheet: $quotationRouter.presentedSheet)
            .tabItem {
                Label("Báo giá", systemImage: "doc.text")
            }

            NavigationStack(path: $productRouter.path) {
                ProductListView()
                    .withSalesDestinations()
            }
            .environment(productRouter)
            .withSalesSheets(sheet: $productRouter.presentedSheet)
            .tabItem {
                Label("Sản phẩm", systemImage: "shippingbox")
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
            case .productDetail(let id):
                ProductDetailView(productID: id)
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
                case .productEditor(let productID):
                    ProductEditorView(productID: productID)
                }
            }
        }
    }
}
