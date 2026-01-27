import Foundation

public protocol TokenStorage {
    var token: String? { get }
    func storeToken(_ token: String) throws
    func removeToken() throws
}

#if os(iOS) || os(macOS)
import Security

public class KeychainTokenStorage: TokenStorage {
    private let service = "com.jobswipe.app"
    private let account = "authToken"

    public var token: String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        if status == errSecSuccess, let data = result as? Data {
            return String(data: data, encoding: .utf8)
        }
        return nil
    }

    public func storeToken(_ token: String) throws {
        guard let data = token.data(using: .utf8) else {
            throw TokenStorageError.invalidToken
        }

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]

        let attributes: [String: Any] = [
            kSecValueData as String: data
        ]

        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)

        if status == errSecItemNotFound {
            let addQuery = query.merging(attributes) { (_, new) in new }
            let addStatus = SecItemAdd(addQuery as CFDictionary, nil)
            if addStatus != errSecSuccess {
                throw TokenStorageError.storageFailed
            }
        } else if status != errSecSuccess {
            throw TokenStorageError.storageFailed
        }
    }

    public func removeToken() throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]

        let status = SecItemDelete(query as CFDictionary)
        if status != errSecSuccess && status != errSecItemNotFound {
            throw TokenStorageError.removalFailed
        }
    }
}
#endif

public class InMemoryTokenStorage: TokenStorage {
    private var storedToken: String?

    public var token: String? {
        return storedToken
    }

    public func storeToken(_ token: String) throws {
        storedToken = token
    }

    public func removeToken() throws {
        storedToken = nil
    }
}

public enum TokenStorageError: Error {
    case invalidToken
    case storageFailed
    case removalFailed
}