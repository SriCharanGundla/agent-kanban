import { describe, expect, it } from "vitest"
import { ApiError, ErrorCode, getErrorMessage } from "./errors"

describe("API error handling", () => {
  it("maps a server error code to an actionable message", () => {
    expect(getErrorMessage(ErrorCode.PROJECT_ACCESS_DENIED)).toBe(
      "You don't have access to this project.",
    )
  })

  it("uses a safe fallback for an unknown server code", () => {
    expect(getErrorMessage("NEW_SERVER_ERROR")).toBe(
      "Something went wrong. Please try again.",
    )
  })

  it("retains the machine-readable code while allowing a custom message", () => {
    const error = new ApiError(ErrorCode.VALIDATION_ERROR, "Title is required")

    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe("ApiError")
    expect(error.code).toBe(ErrorCode.VALIDATION_ERROR)
    expect(error.message).toBe("Title is required")
    expect(error.userMessage).toBe("Please check your input and try again.")
  })
})
