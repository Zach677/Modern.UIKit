import Foundation

extension AppContext {
    static func bootstrap(bundle: Bundle = .main) -> AppContext {
        let bundleIdentifier = bundle.bundleIdentifier ?? "com.example.app"
        let displayName =
            (bundle.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
            ?? (bundle.object(forInfoDictionaryKey: kCFBundleNameKey as String) as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
            ?? "UIKit App"

        let configuration = AppConfiguration(
            bundleIdentifier: bundleIdentifier,
            displayName: displayName
        )
        return AppContext(configuration: configuration)
    }
}
