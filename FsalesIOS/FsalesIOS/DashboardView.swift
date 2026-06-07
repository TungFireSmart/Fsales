import SwiftUI

struct DashboardView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router

    private var openLeadCount: Int {
        store.leads.filter { $0.status != .failed && $0.status != .delivered }.count
    }

    private var pipelineValue: Double {
        store.quotations
            .filter { $0.status == .draft || $0.status == .sent }
            .reduce(0) { $0 + $1.subtotal }
    }

    private var acceptedValue: Double {
        store.quotations
            .filter { $0.status == .accepted }
            .reduce(0) { $0 + $1.subtotal }
    }

    var body: some View {
        List {
            if let error = store.lastSaveError {
                Section {
                    Label(error, systemImage: "exclamationmark.triangle")
                        .foregroundStyle(.orange)
                }
            }

            Section("Hôm nay") {
                HStack(spacing: 12) {
                    MetricTile(title: "Lead mở", value: "\(openLeadCount)", symbol: "person.2")
                    MetricTile(title: "Báo giá", value: "\(store.quotations.count)", symbol: "doc.text")
                }
                HStack(spacing: 12) {
                    MetricTile(title: "Pipeline", value: SalesFormatters.compactMoney(pipelineValue), symbol: "chart.line.uptrend.xyaxis")
                    MetricTile(title: "Đã chốt", value: SalesFormatters.compactMoney(acceptedValue), symbol: "checkmark.seal")
                }
            }

            Section("Việc cần làm") {
                ForEach(store.leads.prefix(5)) { lead in
                    Button {
                        router.navigate(to: .leadDetail(lead.id))
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(lead.customerName)
                                    .font(.headline)
                                Text(lead.needSummary)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)
                            }
                            Spacer()
                            StatusBadge(text: lead.status.displayName)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }

            Section("Thao tác nhanh") {
                Button {
                    router.presentedSheet = .leadEditor(nil)
                } label: {
                    Label("Tạo lead", systemImage: "person.badge.plus")
                }

                Button {
                    router.presentedSheet = .productEditor(nil)
                } label: {
                    Label("Thêm sản phẩm", systemImage: "shippingbox.badge.plus")
                }
            }
        }
        .navigationTitle("FSales")
    }
}

struct MetricTile: View {
    let title: String
    let value: String
    let symbol: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: symbol)
                .font(.headline)
                .foregroundStyle(.blue)
            Text(value)
                .font(.title3.weight(.semibold))
                .lineLimit(1)
                .minimumScaleFactor(0.75)
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}
