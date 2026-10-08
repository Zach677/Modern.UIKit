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

        let navigationController = UINavigationController(rootViewController: RootViewController())
        let window = UIWindow(windowScene: windowScene)
        window.tintColor = .systemBlue
        window.rootViewController = navigationController

        self.window = window
        window.makeKeyAndVisible()
    }
}
