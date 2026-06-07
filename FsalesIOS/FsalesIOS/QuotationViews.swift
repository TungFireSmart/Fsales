import SwiftUI

struct QuotationListView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router

    private var sortedQuotations: [Quotation] {
        store.quotations.sorted { $0.createdAt > $1.createdAt }
    }

    var body: some View {
        List {
            ForEach(sortedQuotations) { quotation in
                Button {
                    router.navigate(to: .quotationDetail(quotation.id))
                } label: {
                    QuotationRowView(quotation: quotation, lead: store.lead(id: quotation.leadID))
                }
                .buttonStyle(.plain)
            }
            .onDelete { offsets in
                store.deleteQuotations(at: offsets, filteredBy: sortedQuotations)
            }
        }
        .navigationTitle("Báo giá")
    }
}

struct QuotationRowView: View {
    let quotation: Quotation
    let lead: Lead?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(quotation.quoteNumber)
                    .font(.headline)
                Spacer()
                StatusBadge(text: quotation.status.displayName)
            }
            Text(lead?.companyName ?? "Không rõ lead")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            HStack {
                Label(SalesFormatters.date(quotation.validUntil), systemImage: "calendar")
                Spacer()
                Text(SalesFormatters.money(quotation.subtotal))
                    .font(.subheadline.weight(.semibold))
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 6)
    }
}

struct QuotationDetailView: View {
    @Environment(SalesStore.self) private var store
    let quotationID: Quotation.ID

    private var quotation: Quotation? {
        store.quotations.first { $0.id == quotationID }
    }

    var body: some View {
        Group {
            if let quotation {
                List {
                    Section("Thông tin") {
                        DetailRow(label: "Số báo giá", value: quotation.quoteNumber)
                        DetailRow(label: "Trạng thái", value: quotation.status.displayName)
                        DetailRow(label: "Hiệu lực", value: SalesFormatters.date(quotation.validUntil))
                    }

                    Section("Khách hàng") {
                        if let lead = store.lead(id: quotation.leadID) {
                            DetailRow(label: "Tên", value: lead.customerName)
                            DetailRow(label: "Công ty", value: lead.companyName)
                            DetailRow(label: "Điện thoại", value: lead.phone)
                        }
                    }

                    Section("Hàng hóa") {
                        ForEach(quotation.lines) { line in
                            VStack(alignment: .leading, spacing: 4) {
                                Text(line.itemName)
                                HStack {
                                    Text("SL \(line.quantity)")
                                    Spacer()
                                    Text(SalesFormatters.money(line.total))
                                }
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            }
                        }
                    }

                    Section("Tổng cộng") {
                        HStack {
                            Text("Thành tiền")
                            Spacer()
                            Text(SalesFormatters.money(quotation.subtotal))
                                .font(.headline)
                        }
                    }

                    Section("Trạng thái") {
                        Button {
                            store.markQuotation(quotation.id, status: .sent)
                        } label: {
                            Label("Đánh dấu đã gửi", systemImage: "paperplane")
                        }

                        Button {
                            store.markQuotation(quotation.id, status: .accepted)
                        } label: {
                            Label("Đánh dấu đã chấp nhận", systemImage: "checkmark.seal")
                        }
                    }

                    if !quotation.note.isEmpty {
                        Section("Ghi chú") {
                            Text(quotation.note)
                        }
                    }
                }
                .navigationTitle(quotation.quoteNumber)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        ShareLink(item: quoteShareText(quotation)) {
                            Image(systemName: "square.and.arrow.up")
                        }
                        .accessibilityLabel("Chia sẻ báo giá")
                    }
                }
            } else {
                ContentUnavailableView("Không tìm thấy báo giá", systemImage: "doc.text.magnifyingglass")
            }
        }
    }

    private func quoteShareText(_ quotation: Quotation) -> String {
        let lead = store.lead(id: quotation.leadID)
        let lines = quotation.lines.map {
            "- \($0.itemName): SL \($0.quantity), \((SalesFormatters.money($0.total)))"
        }.joined(separator: "\n")

        return """
        \(quotation.quoteNumber)
        Khách hàng: \(lead?.customerName ?? "-")
        Công ty: \(lead?.companyName ?? "-")
        Hiệu lực: \(SalesFormatters.date(quotation.validUntil))

        \(lines)

        Tổng cộng: \(SalesFormatters.money(quotation.subtotal))
        Ghi chú: \(quotation.note)
        """
    }
}

struct QuotationEditorView: View {
    @Environment(SalesStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let leadID: Lead.ID

    @State private var quoteNumber = ""
    @State private var status = QuotationStatus.draft
    @State private var validUntil = Date.now.addingTimeInterval(86_400 * 14)
    @State private var note = ""
    @State private var lines: [QuotationLine] = [
        QuotationLine(productID: nil, itemName: "", quantity: 1, unitPrice: 0)
    ]

    private var total: Double {
        lines.reduce(0) { $0 + $1.total }
    }

    var body: some View {
        Form {
            Section("Thông tin") {
                TextField("Số báo giá", text: $quoteNumber)
                Picker("Trạng thái", selection: $status) {
                    ForEach(QuotationStatus.allCases) { status in
                        Text(status.displayName).tag(status)
                    }
                }
                DatePicker("Hiệu lực đến", selection: $validUntil, displayedComponents: .date)
            }

            Section("Hàng hóa") {
                ForEach($lines) { $line in
                    QuotationLineEditor(line: $line)
                }
                .onDelete { offsets in
                    lines.remove(atOffsets: offsets)
                }

                Button {
                    lines.append(QuotationLine(productID: nil, itemName: "", quantity: 1, unitPrice: 0))
                } label: {
                    Label("Thêm dòng", systemImage: "plus")
                }
            }

            Section("Ghi chú") {
                TextEditor(text: $note)
                    .frame(minHeight: 90)
            }

            Section("Tổng cộng") {
                HStack {
                    Text("Thành tiền")
                    Spacer()
                    Text(SalesFormatters.money(total))
                        .font(.headline)
                }
            }
        }
        .navigationTitle("Tạo báo giá")
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Hủy") { dismiss() }
            }
            ToolbarItem(placement: .confirmationAction) {
                Button("Lưu") {
                    save()
                    dismiss()
                }
                .disabled(!canSave)
            }
        }
        .onAppear {
            if quoteNumber.isEmpty {
                quoteNumber = store.nextQuoteNumber()
            }
        }
    }

    private var canSave: Bool {
        !quoteNumber.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && lines.contains { !$0.itemName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
    }

    private func save() {
        let usableLines = lines.filter {
            !$0.itemName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }
        let quotation = Quotation(
            leadID: leadID,
            quoteNumber: quoteNumber,
            status: status,
            validUntil: validUntil,
            note: note,
            lines: usableLines,
            createdAt: .now
        )
        store.upsertQuotation(quotation)
    }
}

struct QuotationLineEditor: View {
    @Environment(SalesStore.self) private var store
    @Binding var line: QuotationLine

    private var activeProducts: [Product] {
        store.products.filter(\.isActive).sorted { $0.name < $1.name }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Picker("Sản phẩm", selection: $line.productID) {
                Text("Tùy chỉnh").tag(nil as Product.ID?)
                ForEach(activeProducts) { product in
                    Text(product.name).tag(Optional(product.id))
                }
            }
            .onChange(of: line.productID) { _, newValue in
                guard let product = store.product(id: newValue) else { return }
                line.itemName = product.name
                line.unitPrice = product.unitPrice
            }

            TextField("Tên hàng hóa", text: $line.itemName)

            HStack {
                Stepper("SL \(line.quantity)", value: $line.quantity, in: 1...999)
                Spacer()
                TextField("Đơn giá", value: $line.unitPrice, format: .number)
                    .keyboardType(.numberPad)
                    .multilineTextAlignment(.trailing)
                    .frame(maxWidth: 140)
            }

            HStack {
                Text("Thành tiền")
                    .foregroundStyle(.secondary)
                Spacer()
                Text(SalesFormatters.money(line.total))
            }
            .font(.caption)
        }
        .padding(.vertical, 4)
    }
}
