import Foundation
import Testing
@testable import ModernUIKit

@Suite(.serialized)
struct AppPreferencesTests {
    @Test
    func bootstrapUsesProvidedBundleMetadata() {
        let bundle = Bundle(for: BundleSentinel.self)

        let preferences = AppPreferences.bootstrap(bundle: bundle)

        #expect(
            preferences.configuration.bundleIdentifier
                == (bundle.bundleIdentifier ?? "com.example.app")
        )
        #expect(
            !preferences.configuration.displayName
                .trimmingCharacters(in: .whitespacesAndNewlines)
                .isEmpty
        )
    }

    @Test
    func rootViewControllerUsesInjectedDisplayName() async {
        await MainActor.run {
            let preferences = AppPreferences(
                configuration: AppConfiguration(
                    bundleIdentifier: "com.example.tests",
                    displayName: "Template App"
                )
            )

            let viewController = RootViewController(preferences: preferences)
            viewController.loadViewIfNeeded()

            #expect(viewController.title == "Template App")
        }
    }
}

private final class BundleSentinel {}
