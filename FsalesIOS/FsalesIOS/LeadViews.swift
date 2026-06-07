import SwiftUI

struct LeadListView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router
    @State private var query = ""

    private var filteredLeads: [Lead] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return store.leads }
        return store.leads.filter {
            $0.customerName.localizedCaseInsensitiveContains(trimmed)
                || $0.companyName.localizedCaseInsensitiveContains(trimmed)
                || $0.phone.localizedCaseInsensitiveContains(trimmed)
        }
    }

    var body: some View {
        List {
            ForEach(filteredLeads) { lead in
                Button {
                    router.navigate(to: .leadDetail(lead.id))
                } label: {
                    LeadRowView(lead: lead, quoteCount: store.quotations(for: lead.id).count)
                }
                .buttonStyle(.plain)
            }
            .onDelete { offsets in
                store.deleteLeads(at: offsets, filteredBy: filteredLeads)
            }
        }
        .searchable(text: $query, prompt: "Tìm lead")
        .navigationTitle("Leads")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    router.presentedSheet = .leadEditor(nil)
                } label: {
                    Image(systemName: "plus")
                }
                .accessibilityLabel("Tạo lead")
            }
        }
    }
}

struct LeadRowView: View {
    let lead: Lead
    let quoteCount: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline) {
                Text(lead.customerName)
                    .font(.headline)
                Spacer()
                StatusBadge(text: lead.status.displayName)
            }

            Text(lead.companyName)
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack {
                Label(lead.phone, systemImage: "phone")
                Spacer()
                Label("\(quoteCount)", systemImage: "doc.text")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 6)
    }
}

struct LeadDetailView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router
    let leadID: Lead.ID

    private var lead: Lead? {
        store.lead(id: leadID)
    }

    var body: some View {
        Group {
            if let lead {
                List {
                    Section("Khách hàng") {
                        DetailRow(label: "Tên", value: lead.customerName)
                        DetailRow(label: "Công ty", value: lead.companyName)
                        DetailRow(label: "Điện thoại", value: lead.phone)
                        DetailRow(label: "Email", value: lead.email)
                        DetailRow(label: "Phụ trách", value: lead.owner)
                        DetailRow(label: "Trạng thái", value: lead.status.displayName)
                    }

                    Section("Nhu cầu") {
                        Text(lead.needSummary.isEmpty ? "Chưa nhập nhu cầu." : lead.needSummary)
                    }

                    Section("Báo giá") {
                        ForEach(store.quotations(for: lead.id)) { quotation in
                            Button {
                                router.navigate(to: .quotationDetail(quotation.id))
                            } label: {
                                HStack {
                                    VStack(alignment: .leading) {
                                        Text(quotation.quoteNumber)
                                        Text(quotation.status.displayName)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    Text(SalesFormatters.money(quotation.subtotal))
                                        .font(.subheadline.weight(.semibold))
                                }
                            }
                        }

                        Button {
                            router.presentedSheet = .quotationEditor(lead.id)
                        } label: {
                            Label("Tạo báo giá", systemImage: "plus")
                        }
                    }
                }
                .navigationTitle(lead.customerName)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button {
                            router.presentedSheet = .leadEditor(lead.id)
                        } label: {
                            Image(systemName: "square.and.pencil")
                        }
                        .accessibilityLabel("Sửa lead")
                    }
                }
            } else {
                ContentUnavailableView("Không tìm thấy lead", systemImage: "person.crop.circle.badge.questionmark")
            }
        }
    }
}

struct LeadEditorView: View {
    @Environment(SalesStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let leadID: Lead.ID?

    @State private var customerName = ""
    @State private var companyName = ""
    @State private var phone = ""
    @State private var email = ""
    @State private var needSummary = ""
    @State private var status = LeadStatus.new
    @State private var owner = ""

    private var title: String {
        leadID == nil ? "Tạo lead" : "Sửa lead"
    }

    var body: some View {
        Form {
            Section("Khách hàng") {
                TextField("Tên khách hàng", text: $customerName)
                TextField("Công ty", text: $companyName)
                TextField("Điện thoại", text: $phone)
                    .keyboardType(.phonePad)
                TextField("Email", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
            }

            Section("Theo dõi") {
                Picker("Trạng thái", selection: $status) {
                    ForEach(LeadStatus.allCases) { status in
                        Text(status.displayName).tag(status)
                    }
                }
                TextField("Phụ trách", text: $owner)
            }

            Section("Nhu cầu") {
                TextEditor(text: $needSummary)
                    .frame(minHeight: 120)
            }
        }
        .navigationTitle(title)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Hủy") { dismiss() }
            }
            ToolbarItem(placement: .confirmationAction) {
                Button("Lưu") {
                    save()
                    dismiss()
                }
                .disabled(customerName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .onAppear(perform: loadExistingLead)
    }

    private func loadExistingLead() {
        guard let leadID, let lead = store.lead(id: leadID) else { return }
        customerName = lead.customerName
        companyName = lead.companyName
        phone = lead.phone
        email = lead.email
        needSummary = lead.needSummary
        status = lead.status
        owner = lead.owner
    }

    private func save() {
        let existing = leadID.flatMap { store.lead(id: $0) }
        let lead = Lead(
            id: existing?.id ?? UUID(),
            customerName: customerName,
            companyName: companyName,
            phone: phone,
            email: email,
            needSummary: needSummary,
            status: status,
            owner: owner,
            createdAt: existing?.createdAt ?? .now,
            lastUpdatedAt: .now
        )
        store.upsertLead(lead)
    }
}

struct StatusBadge: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.caption.weight(.medium))
            .lineLimit(1)
            .minimumScaleFactor(0.8)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.blue.opacity(0.12), in: Capsule())
            .foregroundStyle(.blue)
    }
}

struct DetailRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(label)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value.isEmpty ? "-" : value)
                .multilineTextAlignment(.trailing)
        }
    }
}
