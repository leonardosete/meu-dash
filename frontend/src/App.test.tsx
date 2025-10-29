import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the main app container without crashing", () => {
    const { container } = render(<App />);
    const appContainer = container.querySelector(".app-container");
    expect(appContainer).toBeInTheDocument();
  });
});