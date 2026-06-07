import Foundation
import Observation

@MainActor
@Observable
final class SalesStore {
    var leads: [Lead]
    var quotations: [Quotation]

    init(leads: [Lead] = [], quotations: [Quotation] = []) {
        self.leads = leads
        self.quotations = quotations
    }

    func lead(id: Lead.ID) -> Lead? {
        leads.first { $0.id == id }
    }

    func quotations(for leadID: Lead.ID) -> [Quotation] {
        quotations
            .filter { $0.leadID == leadID }
            .sorted { $0.createdAt > $1.createdAt }
    }

    func upsertLead(_ lead: Lead) {
        if let index = leads.firstIndex(where: { $0.id == lead.id }) {
            leads[index] = lead
        } else {
            leads.insert(lead, at: 0)
        }
    }

    func upsertQuotation(_ quotation: Quotation) {
        if let index = quotations.firstIndex(where: { $0.id == quotation.id }) {
            quotations[index] = quotation
        } else {
            quotations.insert(quotation, at: 0)
        }
        markLeadAsQuoted(quotation.leadID)
    }

    private func markLeadAsQuoted(_ leadID: Lead.ID) {
        guard let index = leads.firstIndex(where: { $0.id == leadID }) else { return }
        if leads[index].status == .new || leads[index].status == .assigned {
            leads[index].status = .quoted
            leads[index].lastUpdatedAt = .now
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

        let quote = Quotation(
            leadID: firstLead.id,
            quoteNumber: "BG-2026-001",
            status: .sent,
            validUntil: .now.addingTimeInterval(86_400 * 14),
            note: "Gia da bao gom VAT, chua bao gom phi van chuyen ngoai TP.",
            lines: [
                QuotationLine(itemName: "Binh chua chay MFZ4", quantity: 12, unitPrice: 280_000),
                QuotationLine(itemName: "Den exit 1 mat", quantity: 8, unitPrice: 390_000),
                QuotationLine(itemName: "Tu cuu hoa trong nha", quantity: 2, unitPrice: 1_850_000)
            ],
            createdAt: .now.addingTimeInterval(-3_600)
        )

        return SalesStore(leads: [firstLead, secondLead], quotations: [quote])
    }
}
