import UIKit

@objc(SceneDelegate)
final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(
        _ scene: UIScene,
        willConnectTo _: UISceneSession,
        options _: UIScene.ConnectionOptions
    ) {
        guard let windowScene = scene as? UIWindowScene else { return }

        let preferences = AppPreferences.bootstrap()
        let rootViewController = RootViewController(preferences: preferences)
        let navigationController = UINavigationController(rootViewController: rootViewController)
        let window = UIWindow(windowScene: windowScene)
        window.tintColor = .systemBlue
        window.rootViewController = navigationController

        self.window = window
        window.makeKeyAndVisible()
    }
}
