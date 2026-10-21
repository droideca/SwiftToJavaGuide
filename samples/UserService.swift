import Foundation

enum ServiceError: Error {
    case notFound
    case invalid(reason: String)
}

struct User: Hashable {
    let id: String
    var name: String
    var email: String?
    var age: Int
}

protocol UserRepository {
    func find(id: String) -> User?
    func save(_ user: User) throws
}

final class UserService {
    private let repo: UserRepository
    private(set) var cache: [String: User] = [:]
    weak var delegate: AnyObject?
    lazy var formatter = DateFormatter()

    init(repo: UserRepository, warmCache: Bool = false) {
        self.repo = repo
    }

    deinit { print("bye") }

    func displayName(for id: String) -> String {
        guard let user = repo.find(id: id) else { return "Unknown" }
        let email = user.email ?? "no email"   // a comment with == inside
        return "\(user.name) <\(email)>"
    }

    func adults(_ users: [User]) -> [String] {
        users.filter { $0.age >= 18 }.map(\.name).sorted()
    }

    func parseAge(_ text: String) -> Int {
        Int(text) ?? 0
    }

    func countWords(_ text: String) -> [String: Int] {
        var counts: [String: Int] = [:]
        for word in text.components(separatedBy: " ") {
            counts[word, default: 0] += 1
        }
        return counts
    }

    func rename(_ user: inout User, to name: String) {
        user.name = name
    }

    func load(id: String, completion: @escaping (Result<User, Error>) -> Void) {
        var attempts = 0
        DispatchQueue.global().async {
            if let user = self.repo.find(id: id) {
                completion(.success(user))
            } else {
                completion(.failure(ServiceError.notFound))
            }
        }
        _ = attempts
    }

    func describe(_ error: ServiceError) -> String {
        switch error {
        case .notFound: return "not found"
        case .invalid(let reason): return reason
        }
    }
}

extension String {
    var isBlankish: Bool { trimmingCharacters(in: .whitespaces).isEmpty }
}
