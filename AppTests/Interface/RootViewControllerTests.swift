@testable import App
import Testing
import UIKit

struct RootViewControllerTests {
    @Test
    func viewLoadsWithContent() {
        let viewController = RootViewController()

        viewController.loadViewIfNeeded()

        #expect(!viewController.view.subviews.isEmpty)
    }
}
