import Foundation

struct AppConfiguration {
    let bundleIdentifier: String
    let displayName: String
}

final class AppContext {
    let configuration: AppConfiguration

    init(configuration: AppConfiguration) {
        self.configuration = configuration
    }
}
