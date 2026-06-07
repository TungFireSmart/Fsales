import SwiftUI

@main
struct FsalesIOSApp: App {
    @State private var store = SalesStore.bootstrap()

    var body: some Scene {
        WindowGroup {
            AppShellView()
                .environment(store)
        }
    }
}
