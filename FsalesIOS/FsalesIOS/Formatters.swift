import Foundation

enum SalesFormatters {
    static let currency: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "VND"
        formatter.maximumFractionDigits = 0
        formatter.locale = Locale(identifier: "vi_VN")
        return formatter
    }()

    static let shortDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .none
        formatter.locale = Locale(identifier: "vi_VN")
        return formatter
    }()

    static func money(_ value: Double) -> String {
        currency.string(from: NSNumber(value: value)) ?? "\(value)"
    }

    static func compactMoney(_ value: Double) -> String {
        if value >= 1_000_000_000 {
            return String(format: "%.1f tỷ", value / 1_000_000_000)
        }
        if value >= 1_000_000 {
            return String(format: "%.1f tr", value / 1_000_000)
        }
        return money(value)
    }

    static func date(_ value: Date) -> String {
        shortDate.string(from: value)
    }
}
