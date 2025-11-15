import { expect, afterEach, beforeAll, afterAll, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";

expect.extend(matchers);

afterEach(() => {
  cleanup();
});

let originalFetch: typeof fetch | undefined;

beforeAll(() => {
  originalFetch = globalThis.fetch;
});

afterAll(() => {
  vi.unstubAllGlobals();
  if (originalFetch) {
    globalThis.fetch = originalFetch;
  }
});
