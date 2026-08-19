import { afterEach, describe, expect, it, vi } from "vitest"
import { copyToClipboard } from "./clipboard"

describe("copyToClipboard", () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("uses the Clipboard API in a secure context", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(window, "isSecureContext", {
      configurable: true,
      value: true,
    })
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    })

    await expect(copyToClipboard("task-id")).resolves.toBe(true)
    expect(writeText).toHaveBeenCalledWith("task-id")
  })

  it("falls back to execCommand when the Clipboard API rejects", async () => {
    Object.defineProperty(window, "isSecureContext", {
      configurable: true,
      value: true,
    })
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    })
    const execCommand = vi.fn().mockReturnValue(true)
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    })

    await expect(copyToClipboard("fallback-value")).resolves.toBe(true)
    expect(execCommand).toHaveBeenCalledWith("copy")
    expect(document.querySelector("textarea")).not.toBeInTheDocument()
  })
})
