import Foundation
import Observation

@MainActor
@Observable
final class SalesStore {
    var leads: [Lead]
    var products: [Product]
    var quotations: [Quotation]
    var orders: [SalesOrder]
    var lastSaveError: String?

    init(leads: [Lead] = [], products: [Product] = [], quotations: [Quotation] = [], orders: [SalesOrder] = []) {
        self.leads = leads
        self.products = products
        self.quotations = quotations
        self.orders = orders
    }

    static func bootstrap() -> SalesStore {
        do {
            if let snapshot = try SalesPersistence.load() {
                return SalesStore(
                    leads: snapshot.leads,
                    products: snapshot.products,
                    quotations: snapshot.quotations,
                    orders: snapshot.orders
                )
            }
        } catch {
            let store = SalesStore.preview
            store.lastSaveError = "Khong the nap du lieu cuc bo: \(error.localizedDescription)"
            return store
        }
        return .preview
    }

    func lead(id: Lead.ID) -> Lead? {
        leads.first { $0.id == id }
    }

    func quotations(for leadID: Lead.ID) -> [Quotation] {
        quotations
            .filter { $0.leadID == leadID }
            .sorted { $0.createdAt > $1.createdAt }
    }

    func product(id: Product.ID?) -> Product? {
        guard let id else { return nil }
        return products.first { $0.id == id }
    }

    func order(id: SalesOrder.ID) -> SalesOrder? {
        orders.first { $0.id == id }
    }

    func order(for quotationID: Quotation.ID) -> SalesOrder? {
        orders.first { $0.quotationID == quotationID }
    }

    func upsertLead(_ lead: Lead) {
        if let index = leads.firstIndex(where: { $0.id == lead.id }) {
            leads[index] = lead
        } else {
            leads.insert(lead, at: 0)
        }
        save()
    }

    func upsertProduct(_ product: Product) {
        if let index = products.firstIndex(where: { $0.id == product.id }) {
            products[index] = product
        } else {
            products.insert(product, at: 0)
        }
        save()
    }

    func upsertQuotation(_ quotation: Quotation) {
        if let index = quotations.firstIndex(where: { $0.id == quotation.id }) {
            quotations[index] = quotation
        } else {
            quotations.insert(quotation, at: 0)
        }
        markLeadAsQuoted(quotation.leadID)
        save()
    }

    func deleteLeads(at offsets: IndexSet, filteredBy visibleLeads: [Lead]? = nil) {
        let removedIDs: [Lead.ID]
        if let visibleLeads {
            removedIDs = offsets.map { visibleLeads[$0].id }
            leads.removeAll { removedIDs.contains($0.id) }
        } else {
            removedIDs = offsets.map { leads[$0].id }
            remove(from: &leads, at: offsets)
        }
        quotations.removeAll { removedIDs.contains($0.leadID) }
        orders.removeAll { removedIDs.contains($0.leadID) }
        save()
    }

    func deleteProducts(at offsets: IndexSet, filteredBy visibleProducts: [Product]? = nil) {
        if let visibleProducts {
            let removedIDs = offsets.map { visibleProducts[$0].id }
            products.removeAll { removedIDs.contains($0.id) }
        } else {
            remove(from: &products, at: offsets)
        }
        save()
    }

    func deleteQuotations(at offsets: IndexSet, filteredBy visibleQuotations: [Quotation]? = nil) {
        if let visibleQuotations {
            let removedIDs = offsets.map { visibleQuotations[$0].id }
            quotations.removeAll { removedIDs.contains($0.id) }
        } else {
            remove(from: &quotations, at: offsets)
        }
        save()
    }

    func deleteOrders(at offsets: IndexSet, filteredBy visibleOrders: [SalesOrder]? = nil) {
        if let visibleOrders {
            let removedIDs = offsets.map { visibleOrders[$0].id }
            orders.removeAll { removedIDs.contains($0.id) }
        } else {
            remove(from: &orders, at: offsets)
        }
        save()
    }

    func markQuotation(_ quotationID: Quotation.ID, status: QuotationStatus) {
        guard let index = quotations.firstIndex(where: { $0.id == quotationID }) else { return }
        quotations[index].status = status
        if status == .accepted, let leadIndex = leads.firstIndex(where: { $0.id == quotations[index].leadID }) {
            leads[leadIndex].status = .ordered
            leads[leadIndex].lastUpdatedAt = .now
        }
        save()
    }

    func nextQuoteNumber() -> String {
        let year = Calendar.current.component(.year, from: .now)
        let next = quotations.count + 1
        return "BG-\(year)-\(String(format: "%03d", next))"
    }

    func nextOrderNumber() -> String {
        let year = Calendar.current.component(.year, from: .now)
        let next = orders.count + 1
        return "DH-\(year)-\(String(format: "%03d", next))"
    }

    @discardableResult
    func createOrder(from quotationID: Quotation.ID) -> SalesOrder? {
        guard let quotation = quotations.first(where: { $0.id == quotationID }) else { return nil }
        if let existing = order(for: quotationID) {
            return existing
        }

        let order = SalesOrder(
            quotationID: quotation.id,
            leadID: quotation.leadID,
            orderNumber: nextOrderNumber(),
            status: .new,
            note: quotation.note,
            lines: quotation.lines,
            createdAt: .now
        )
        orders.insert(order, at: 0)
        markQuotation(quotation.id, status: .accepted)
        reserveStock(for: quotation.lines)
        save()
        return order
    }

    func markOrder(_ orderID: SalesOrder.ID, status: OrderStatus) {
        guard let index = orders.firstIndex(where: { $0.id == orderID }) else { return }
        orders[index].status = status
        if let leadIndex = leads.firstIndex(where: { $0.id == orders[index].leadID }) {
            switch status {
            case .delivered:
                leads[leadIndex].status = .delivered
            case .paid:
                leads[leadIndex].status = .paid
            case .cancelled:
                leads[leadIndex].status = .failed
            case .new, .confirmed:
                leads[leadIndex].status = .ordered
            }
            leads[leadIndex].lastUpdatedAt = .now
        }
        save()
    }

    private func markLeadAsQuoted(_ leadID: Lead.ID) {
        guard let index = leads.firstIndex(where: { $0.id == leadID }) else { return }
        if leads[index].status == .new || leads[index].status == .assigned {
            leads[index].status = .quoted
            leads[index].lastUpdatedAt = .now
        }
    }

    private func save() {
        do {
            try SalesPersistence.save(SalesSnapshot(leads: leads, products: products, quotations: quotations, orders: orders))
            lastSaveError = nil
        } catch {
            lastSaveError = error.localizedDescription
        }
    }

    private func remove<Element>(from array: inout [Element], at offsets: IndexSet) {
        for offset in offsets.sorted(by: >) {
            array.remove(at: offset)
        }
    }

    private func reserveStock(for lines: [QuotationLine]) {
        for line in lines {
            guard let productID = line.productID,
                  let index = products.firstIndex(where: { $0.id == productID })
            else { continue }
            products[index].stockQuantity = max(0, products[index].stockQuantity - line.quantity)
        }
    }
}

extension SalesStore {
    static var preview: SalesStore {
        let firstLead = Lead(
            customerName: "Nguyen Van An",
            companyName: "PCCC Minh An",
            phone: "0901 234 567",
            email: "an@example.com",
            needSummary: "Bao gia binh chua chay, tu cuu hoa va den exit cho nha xuong.",
            status: .quoted,
            owner: "Sales 01",
            createdAt: .now.addingTimeInterval(-86_400 * 2),
            lastUpdatedAt: .now.addingTimeInterval(-3_600)
        )

        let secondLead = Lead(
            customerName: "Tran Thi Binh",
            companyName: "Kho van Binh Phu",
            phone: "0918 555 222",
            email: "binh@example.com",
            needSummary: "Tu van danh muc thiet bi PCCC cho kho hang moi.",
            status: .assigned,
            owner: "Sales 02",
            createdAt: .now.addingTimeInterval(-86_400),
            lastUpdatedAt: .now.addingTimeInterval(-7_200)
        )

        let products = [
            Product(code: "MFZ4", name: "Binh chua chay MFZ4", category: "Binh chua chay", unit: "binh", unitPrice: 280_000, stockQuantity: 40, isActive: true),
            Product(code: "EXIT-1", name: "Den exit 1 mat", category: "Den su co", unit: "cai", unitPrice: 390_000, stockQuantity: 24, isActive: true),
            Product(code: "TCH-01", name: "Tu cuu hoa trong nha", category: "Tu PCCC", unit: "tu", unitPrice: 1_850_000, stockQuantity: 8, isActive: true)
        ]

        let quote = Quotation(
            leadID: firstLead.id,
            quoteNumber: "BG-2026-001",
            status: .sent,
            validUntil: .now.addingTimeInterval(86_400 * 14),
            note: "Gia da bao gom VAT, chua bao gom phi van chuyen ngoai TP.",
            lines: [
                QuotationLine(productID: products[0].id, itemName: products[0].name, quantity: 12, unitPrice: products[0].unitPrice),
                QuotationLine(productID: products[1].id, itemName: products[1].name, quantity: 8, unitPrice: products[1].unitPrice),
                QuotationLine(productID: products[2].id, itemName: products[2].name, quantity: 2, unitPrice: products[2].unitPrice)
            ],
            createdAt: .now.addingTimeInterval(-3_600)
        )

        return SalesStore(leads: [firstLead, secondLead], products: products, quotations: [quote])
    }
}
