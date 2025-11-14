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

  const mockedFetch: typeof fetch = async (input, init) => {
    let url: string;

    if (typeof input === "string") {
      url = input;
    } else if (input instanceof URL) {
      url = input.toString();
    } else {
      url = input.url;
    }

    if (url.endsWith("/health")) {
      return new Response(
        JSON.stringify({ version: "test" }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    if (originalFetch) {
      return originalFetch(input as RequestInfo, init);
    }

    throw new Error("fetch não está disponível no ambiente de teste");
  };

  vi.stubGlobal("fetch", mockedFetch);
});

afterAll(() => {
  vi.unstubAllGlobals();
  if (originalFetch) {
    globalThis.fetch = originalFetch;
  }
});
