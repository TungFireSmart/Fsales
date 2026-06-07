import Foundation

enum LeadStatus: String, CaseIterable, Identifiable, Codable {
    case new = "Moi"
    case assigned = "Da nhan viec"
    case quoted = "Da bao gia"
    case ordered = "Da dat hang"
    case paid = "Da thanh toan"
    case delivered = "Da giao hang"
    case failed = "Done - That bai"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .new: "Mới"
        case .assigned: "Đã nhận việc"
        case .quoted: "Đã báo giá"
        case .ordered: "Đã đặt hàng"
        case .paid: "Đã thanh toán"
        case .delivered: "Đã giao hàng"
        case .failed: "Done - Thất bại"
        }
    }
}

enum QuotationStatus: String, CaseIterable, Identifiable, Codable {
    case draft = "Nhap"
    case sent = "Da gui"
    case accepted = "Da chap nhan"
    case expired = "Het han"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .draft: "Nháp"
        case .sent: "Đã gửi"
        case .accepted: "Đã chấp nhận"
        case .expired: "Hết hạn"
        }
    }
}

struct Lead: Identifiable, Hashable, Codable {
    var id = UUID()
    var customerName: String
    var companyName: String
    var phone: String
    var email: String
    var needSummary: String
    var status: LeadStatus
    var owner: String
    var createdAt: Date
    var lastUpdatedAt: Date
}

struct Product: Identifiable, Hashable, Codable {
    var id = UUID()
    var code: String
    var name: String
    var category: String
    var unit: String
    var unitPrice: Double
    var stockQuantity: Int
    var isActive: Bool
}

struct QuotationLine: Identifiable, Hashable, Codable {
    var id = UUID()
    var productID: Product.ID?
    var itemName: String
    var quantity: Int
    var unitPrice: Double

    var total: Double {
        unitPrice * Double(quantity)
    }
}

struct Quotation: Identifiable, Hashable, Codable {
    var id = UUID()
    var leadID: Lead.ID
    var quoteNumber: String
    var status: QuotationStatus
    var validUntil: Date
    var note: String
    var lines: [QuotationLine]
    var createdAt: Date

    var subtotal: Double {
        lines.reduce(0) { $0 + $1.total }
    }
}

struct SalesSnapshot: Codable {
    var leads: [Lead]
    var products: [Product]
    var quotations: [Quotation]
}
