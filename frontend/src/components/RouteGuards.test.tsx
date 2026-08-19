import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { ProtectedRoute } from "./ProtectedRoute"
import { PublicRoute } from "./PublicRoute"
import { useAuth } from "@/context/AuthContext"

vi.mock("@/context/AuthContext", () => ({
  useAuth: vi.fn(),
}))

const mockedUseAuth = vi.mocked(useAuth)

function setAuthState(isAuthenticated: boolean, isLoading = false) {
  mockedUseAuth.mockReturnValue({
    user: null,
    isAuthenticated,
    isLoading,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(),
  })
}

describe("route guards", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("redirects unauthenticated visitors away from protected pages", () => {
    setAuthState(false)

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>Private dashboard</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText("Login page")).toBeInTheDocument()
    expect(screen.queryByText("Private dashboard")).not.toBeInTheDocument()
  })

  it("renders protected content for authenticated users", () => {
    setAuthState(true)

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Private dashboard</div>
        </ProtectedRoute>
      </MemoryRouter>,
    )

    expect(screen.getByText("Private dashboard")).toBeInTheDocument()
  })

  it("redirects authenticated users away from public auth pages", () => {
    setAuthState(true)

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/dashboard" element={<div>Dashboard page</div>} />
          <Route
            path="/login"
            element={
              <PublicRoute>
                <div>Login form</div>
              </PublicRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText("Dashboard page")).toBeInTheDocument()
    expect(screen.queryByText("Login form")).not.toBeInTheDocument()
  })

  it("shows a stable loading state while authentication initializes", () => {
    setAuthState(false, true)

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Private dashboard</div>
        </ProtectedRoute>
      </MemoryRouter>,
    )

    expect(screen.getByText("Loading...")).toBeInTheDocument()
    expect(screen.queryByText("Private dashboard")).not.toBeInTheDocument()
  })
})
