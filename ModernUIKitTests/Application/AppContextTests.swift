import Foundation
import Testing
@testable import ModernUIKit

@Suite(.serialized)
struct AppContextTests {
    @Test
    func bootstrapUsesProvidedBundleMetadata() {
        let bundle = Bundle(for: BundleSentinel.self)

        let context = AppContext.bootstrap(bundle: bundle)

        #expect(
            context.configuration.bundleIdentifier
                == (bundle.bundleIdentifier ?? "com.example.app")
        )
        #expect(
            !context.configuration.displayName
                .trimmingCharacters(in: .whitespacesAndNewlines)
                .isEmpty
        )
    }

    @Test
    func rootViewControllerUsesInjectedDisplayName() async {
        await MainActor.run {
            let context = AppContext(
                configuration: AppConfiguration(
                    bundleIdentifier: "com.example.tests",
                    displayName: "Template App"
                )
            )

            let viewController = RootViewController(appContext: context)
            viewController.loadViewIfNeeded()

            #expect(viewController.title == "Template App")
        }
    }
}

private final class BundleSentinel {}
