import UIKit

@objc(SceneDelegate)
final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    private var appContext: AppContext?

    func scene(
        _ scene: UIScene,
        willConnectTo _: UISceneSession,
        options _: UIScene.ConnectionOptions
    ) {
        guard let windowScene = scene as? UIWindowScene else { return }

        let appContext = AppContext.bootstrap()
        let rootViewController = RootViewController(appContext: appContext)
        let navigationController = UINavigationController(rootViewController: rootViewController)
        let window = UIWindow(windowScene: windowScene)
        window.tintColor = .systemBlue
        window.rootViewController = navigationController

        self.appContext = appContext
        self.window = window
        window.makeKeyAndVisible()
    }
}
