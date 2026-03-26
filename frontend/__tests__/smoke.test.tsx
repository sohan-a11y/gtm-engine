import { render, screen } from "@testing-library/react";

import { Button } from "@/components/ui/button";

describe("frontend scaffold", () => {
  it("renders shared UI primitives", () => {
    render(<Button>Launch Pipeline</Button>);
    expect(screen.getByRole("button", { name: "Launch Pipeline" })).toBeInTheDocument();
  });
});
