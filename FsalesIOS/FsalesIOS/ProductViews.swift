import SwiftUI

struct ProductListView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router
    @State private var query = ""

    private var filteredProducts: [Product] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return store.products }
        return store.products.filter {
            $0.name.localizedCaseInsensitiveContains(trimmed)
                || $0.code.localizedCaseInsensitiveContains(trimmed)
                || $0.category.localizedCaseInsensitiveContains(trimmed)
        }
    }

    var body: some View {
        List {
            ForEach(filteredProducts) { product in
                Button {
                    router.navigate(to: .productDetail(product.id))
                } label: {
                    ProductRowView(product: product)
                }
                .buttonStyle(.plain)
            }
            .onDelete { offsets in
                store.deleteProducts(at: offsets, filteredBy: filteredProducts)
            }
        }
        .searchable(text: $query, prompt: "Tìm sản phẩm")
        .navigationTitle("Sản phẩm")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    router.presentedSheet = .productEditor(nil)
                } label: {
                    Image(systemName: "plus")
                }
                .accessibilityLabel("Thêm sản phẩm")
            }
        }
    }
}

struct ProductRowView: View {
    let product: Product

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(product.name)
                    .font(.headline)
                Spacer()
                Text(product.code)
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
            }

            HStack {
                Text(product.category)
                Spacer()
                Text(SalesFormatters.money(product.unitPrice))
                    .fontWeight(.semibold)
            }
            .font(.subheadline)
            .foregroundStyle(.secondary)

            HStack {
                Label("\(product.stockQuantity) \(product.unit)", systemImage: "archivebox")
                Spacer()
                if !product.isActive {
                    StatusBadge(text: "Ngừng bán")
                }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 6)
    }
}

struct ProductDetailView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router
    let productID: Product.ID

    private var product: Product? {
        store.product(id: productID)
    }

    var body: some View {
        Group {
            if let product {
                List {
                    Section("Thông tin") {
                        DetailRow(label: "Mã", value: product.code)
                        DetailRow(label: "Tên", value: product.name)
                        DetailRow(label: "Nhóm", value: product.category)
                        DetailRow(label: "Đơn vị", value: product.unit)
                        DetailRow(label: "Giá", value: SalesFormatters.money(product.unitPrice))
                        DetailRow(label: "Tồn", value: "\(product.stockQuantity)")
                        DetailRow(label: "Trạng thái", value: product.isActive ? "Đang bán" : "Ngừng bán")
                    }
                }
                .navigationTitle(product.name)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button {
                            router.presentedSheet = .productEditor(product.id)
                        } label: {
                            Image(systemName: "square.and.pencil")
                        }
                        .accessibilityLabel("Sửa sản phẩm")
                    }
                }
            } else {
                ContentUnavailableView("Không tìm thấy sản phẩm", systemImage: "shippingbox")
            }
        }
    }
}

struct ProductEditorView: View {
    @Environment(SalesStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let productID: Product.ID?

    @State private var code = ""
    @State private var name = ""
    @State private var category = ""
    @State private var unit = "cái"
    @State private var unitPrice = 0.0
    @State private var stockQuantity = 0
    @State private var isActive = true

    private var title: String {
        productID == nil ? "Thêm sản phẩm" : "Sửa sản phẩm"
    }

    var body: some View {
        Form {
            Section("Thông tin") {
                TextField("Mã hàng", text: $code)
                    .textInputAutocapitalization(.characters)
                TextField("Tên hàng hóa", text: $name)
                TextField("Nhóm", text: $category)
                TextField("Đơn vị", text: $unit)
            }

            Section("Giá và tồn") {
                TextField("Đơn giá", value: $unitPrice, format: .number)
                    .keyboardType(.numberPad)
                Stepper("Tồn kho \(stockQuantity)", value: $stockQuantity, in: 0...999_999)
                Toggle("Đang bán", isOn: $isActive)
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
                .disabled(name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .onAppear(perform: loadExistingProduct)
    }

    private func loadExistingProduct() {
        guard let productID, let product = store.product(id: productID) else { return }
        code = product.code
        name = product.name
        category = product.category
        unit = product.unit
        unitPrice = product.unitPrice
        stockQuantity = product.stockQuantity
        isActive = product.isActive
    }

    private func save() {
        let existing = productID.flatMap { store.product(id: $0) }
        let product = Product(
            id: existing?.id ?? UUID(),
            code: code.isEmpty ? name.prefix(8).uppercased() : code,
            name: name,
            category: category,
            unit: unit,
            unitPrice: unitPrice,
            stockQuantity: stockQuantity,
            isActive: isActive
        )
        store.upsertProduct(product)
    }
}
