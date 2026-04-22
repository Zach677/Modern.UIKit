import XCTest
@testable import No_StoryBoard

@MainActor
final class AppContextTests: XCTestCase {
    func testBootstrapUsesProvidedBundleMetadata() {
        let bundle = Bundle(for: Self.self)

        let context = AppContext.bootstrap(bundle: bundle)

        XCTAssertEqual(
            context.configuration.bundleIdentifier,
            bundle.bundleIdentifier ?? "com.example.app"
        )
        XCTAssertFalse(
            context.configuration.displayName
                .trimmingCharacters(in: .whitespacesAndNewlines)
                .isEmpty
        )
    }

    func testRootViewControllerUsesInjectedDisplayName() {
        let context = AppContext(
            configuration: AppConfiguration(
                bundleIdentifier: "com.example.tests",
                displayName: "Template App"
            )
        )

        let viewController = RootViewController(appContext: context)
        viewController.loadViewIfNeeded()

        XCTAssertEqual(viewController.title, "Template App")
    }
}
