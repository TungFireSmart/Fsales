import SwiftUI

struct OrderListView: View {
    @Environment(SalesStore.self) private var store
    @Environment(SalesRouter.self) private var router

    private var sortedOrders: [SalesOrder] {
        store.orders.sorted { $0.createdAt > $1.createdAt }
    }

    var body: some View {
        List {
            ForEach(sortedOrders) { order in
                Button {
                    router.navigate(to: .orderDetail(order.id))
                } label: {
                    OrderRowView(order: order, lead: store.lead(id: order.leadID))
                }
                .buttonStyle(.plain)
            }
            .onDelete { offsets in
                store.deleteOrders(at: offsets, filteredBy: sortedOrders)
            }
        }
        .navigationTitle("Đơn hàng")
    }
}

struct OrderRowView: View {
    let order: SalesOrder
    let lead: Lead?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(order.orderNumber)
                    .font(.headline)
                Spacer()
                StatusBadge(text: order.status.displayName)
            }

            Text(lead?.companyName ?? "Không rõ khách hàng")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack {
                Label(SalesFormatters.date(order.createdAt), systemImage: "calendar")
                Spacer()
                Text(SalesFormatters.money(order.subtotal))
                    .font(.subheadline.weight(.semibold))
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 6)
    }
}

struct OrderDetailView: View {
    @Environment(SalesStore.self) private var store
    let orderID: SalesOrder.ID

    private var order: SalesOrder? {
        store.order(id: orderID)
    }

    var body: some View {
        Group {
            if let order {
                List {
                    Section("Thông tin") {
                        DetailRow(label: "Số đơn", value: order.orderNumber)
                        DetailRow(label: "Trạng thái", value: order.status.displayName)
                        DetailRow(label: "Ngày tạo", value: SalesFormatters.date(order.createdAt))
                    }

                    Section("Khách hàng") {
                        if let lead = store.lead(id: order.leadID) {
                            DetailRow(label: "Tên", value: lead.customerName)
                            DetailRow(label: "Công ty", value: lead.companyName)
                            DetailRow(label: "Điện thoại", value: lead.phone)
                        }
                    }

                    Section("Hàng hóa") {
                        ForEach(order.lines) { line in
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
                            Text(SalesFormatters.money(order.subtotal))
                                .font(.headline)
                        }
                    }

                    Section("Cập nhật") {
                        Button {
                            store.markOrder(order.id, status: .confirmed)
                        } label: {
                            Label("Đã xác nhận", systemImage: "checkmark.circle")
                        }

                        Button {
                            store.markOrder(order.id, status: .delivered)
                        } label: {
                            Label("Đã giao hàng", systemImage: "truck.box")
                        }

                        Button {
                            store.markOrder(order.id, status: .paid)
                        } label: {
                            Label("Đã thanh toán", systemImage: "creditcard")
                        }

                        Button(role: .destructive) {
                            store.markOrder(order.id, status: .cancelled)
                        } label: {
                            Label("Hủy đơn", systemImage: "xmark.circle")
                        }
                    }

                    if !order.note.isEmpty {
                        Section("Ghi chú") {
                            Text(order.note)
                        }
                    }
                }
                .navigationTitle(order.orderNumber)
            } else {
                ContentUnavailableView("Không tìm thấy đơn hàng", systemImage: "cart")
            }
        }
    }
}
