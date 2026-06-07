import Foundation

enum SalesPersistence {
    private static let fileName = "fsales-ios-data.json"

    static var fileURL: URL {
        let directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("FsalesIOS", isDirectory: true)
        return directory.appendingPathComponent(fileName)
    }

    static func load() throws -> SalesSnapshot? {
        let url = fileURL
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        let data = try Data(contentsOf: url)
        return try JSONDecoder.sales.decode(SalesSnapshot.self, from: data)
    }

    static func save(_ snapshot: SalesSnapshot) throws {
        let url = fileURL
        try FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        let data = try JSONEncoder.sales.encode(snapshot)
        try data.write(to: url, options: [.atomic])
    }
}

private extension JSONEncoder {
    static var sales: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return encoder
    }
}

private extension JSONDecoder {
    static var sales: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}
