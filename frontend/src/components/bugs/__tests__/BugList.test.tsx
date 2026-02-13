/**
 * Unit tests for BugList component
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { BugList } from "../BugList";
import type { Bug, BugMatch } from "../../../types/bug";
import { BugSeverity, BugCategory } from "../../../types/bug";

describe("BugList", () => {
  const mockBugs: Bug[] = [
    {
      bug_number: "13364795",
      title: "Wrong results with optimizer_adaptive_features",
      category: BugCategory.OPTIMIZER,
      severity: BugSeverity.CRITICAL,
      description: "Critical optimizer bug",
      symptoms: ["Incorrect results"],
      affected_versions: ["12.1.0.1"],
      fixed_versions: ["12.2.0.1"],
      workarounds: ["Set parameter to false"],
      remediation_sql: "ALTER SESSION SET optimizer_adaptive_features=false;",
    },
    {
      bug_number: "19396364",
      title: "Parallel query hangs",
      category: BugCategory.PARALLEL,
      severity: BugSeverity.HIGH,
      description: "Parallel execution issue",
      symptoms: ["Query hangs"],
      affected_versions: ["12.1.0.2"],
      fixed_versions: ["12.2.0.1"],
      workarounds: ["Disable parallel"],
    },
    {
      bug_number: "17202207",
      title: "ORA-00600 in parse loop",
      category: BugCategory.PARSING,
      severity: BugSeverity.MEDIUM,
      description: "Parse error bug",
      symptoms: ["ORA-00600 error"],
      affected_versions: ["11.2.0.4"],
      fixed_versions: ["12.1.0.1"],
      workarounds: ["Apply patch"],
    },
  ];

  const mockMatches: BugMatch[] = [
    {
      bug: mockBugs[0],
      confidence: 85,
      matched_patterns: ["execution_plan"],
      evidence: {},
      sql_id: "abc123def4567",
    },
  ];

  it("renders bug list with all bugs", () => {
    render(<BugList bugs={mockBugs} />);

    expect(screen.getByText("Bug 13364795")).toBeInTheDocument();
    expect(screen.getByText("Bug 19396364")).toBeInTheDocument();
    expect(screen.getByText("Bug 17202207")).toBeInTheDocument();
  });

  it("displays statistics correctly", () => {
    render(<BugList bugs={mockBugs} showStats={true} />);

    expect(screen.getByText("Total")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument(); // Total count
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // Critical count
  });

  it("does not display statistics when showStats is false", () => {
    render(<BugList bugs={mockBugs} showStats={false} />);

    expect(screen.queryByText("Total")).not.toBeInTheDocument();
  });

  it("filters bugs by search text", async () => {
    render(<BugList bugs={mockBugs} />);

    const searchInput = screen.getByPlaceholderText("Search bugs...");
    fireEvent.change(searchInput, { target: { value: "optimizer" } });

    await waitFor(() => {
      expect(screen.getByText("Bug 13364795")).toBeInTheDocument();
      expect(screen.queryByText("Bug 19396364")).not.toBeInTheDocument();
      expect(screen.queryByText("Bug 17202207")).not.toBeInTheDocument();
    });
  });

  it("filters bugs by severity", async () => {
    const handleFilterChange = jest.fn();
    render(<BugList bugs={mockBugs} onFilterChange={handleFilterChange} />);

    const severitySelect = screen.getByPlaceholderText("Filter by severity");
    fireEvent.click(severitySelect);

    const criticalOption = await screen.findByText("Critical");
    fireEvent.click(criticalOption);

    expect(handleFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ severity: BugSeverity.CRITICAL })
    );
  });

  it("filters bugs by category", async () => {
    const handleFilterChange = jest.fn();
    render(<BugList bugs={mockBugs} onFilterChange={handleFilterChange} />);

    const categorySelect = screen.getByPlaceholderText("Filter by category");
    fireEvent.click(categorySelect);

    const optimizerOption = await screen.findByText("Optimizer");
    fireEvent.click(optimizerOption);

    expect(handleFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ category: BugCategory.OPTIMIZER })
    );
  });

  it("displays empty state when no bugs found", () => {
    render(<BugList bugs={[]} />);

    expect(screen.getByText("No bugs found")).toBeInTheDocument();
  });

  it("displays loading spinner when loading", () => {
    render(<BugList bugs={[]} loading={true} />);

    expect(screen.getByRole("img", { hidden: true })).toBeInTheDocument(); // Ant Design Spin
  });

  it("displays error alert when error occurs", () => {
    const error = new Error("Failed to load bugs");
    render(<BugList bugs={[]} error={error} />);

    expect(screen.getByText("Error Loading Bugs")).toBeInTheDocument();
    expect(screen.getByText("Failed to load bugs")).toBeInTheDocument();
  });

  it("shows confidence when showConfidence is true and matches provided", () => {
    render(
      <BugList bugs={mockBugs} matches={mockMatches} showConfidence={true} />
    );

    expect(screen.getByText(/85%/)).toBeInTheDocument();
    expect(screen.getByText(/High/)).toBeInTheDocument();
  });

  it("opens modal when bug card is clicked", async () => {
    render(<BugList bugs={mockBugs} />);

    const bugCard = screen.getByText("Bug 13364795");
    fireEvent.click(bugCard.closest(".ant-card")!);

    await waitFor(() => {
      // Modal should be visible
      expect(screen.getAllByText("Bug 13364795").length).toBeGreaterThan(1);
    });
  });

  it("closes modal when close button is clicked", async () => {
    render(<BugList bugs={mockBugs} />);

    // Open modal
    const bugCard = screen.getByText("Bug 13364795");
    fireEvent.click(bugCard.closest(".ant-card")!);

    await waitFor(() => {
      expect(screen.getAllByText("Bug 13364795").length).toBeGreaterThan(1);
    });

    // Close modal
    const closeButton = screen.getByRole("button", { name: /Close/i });
    fireEvent.click(closeButton);

    await waitFor(() => {
      // Modal should be closed (only one instance of bug number visible)
      expect(screen.getAllByText("Bug 13364795").length).toBe(1);
    });
  });

  it("clears search when clear button is clicked", async () => {
    render(<BugList bugs={mockBugs} />);

    const searchInput = screen.getByPlaceholderText("Search bugs...");
    fireEvent.change(searchInput, { target: { value: "optimizer" } });

    await waitFor(() => {
      expect(screen.queryByText("Bug 19396364")).not.toBeInTheDocument();
    });

    // Clear search
    const clearButton = searchInput.parentElement?.querySelector(".anticon-close-circle");
    if (clearButton) {
      fireEvent.click(clearButton);
    }

    await waitFor(() => {
      expect(screen.getByText("Bug 19396364")).toBeInTheDocument();
    });
  });

  it("calculates statistics correctly for filtered bugs", () => {
    render(<BugList bugs={mockBugs} showStats={true} />);

    // Total bugs
    const totalStat = screen.getByText("Total").closest(".ant-statistic");
    expect(totalStat).toHaveTextContent("3");

    // Critical bugs
    const criticalStat = screen.getByText("Critical").closest(".ant-statistic");
    expect(criticalStat).toHaveTextContent("1");

    // High severity bugs
    const highStat = screen.getByText("High").closest(".ant-statistic");
    expect(highStat).toHaveTextContent("1");

    // Medium severity bugs
    const mediumStat = screen.getByText("Medium").closest(".ant-statistic");
    expect(mediumStat).toHaveTextContent("1");
  });

  it("search is case insensitive", async () => {
    render(<BugList bugs={mockBugs} />);

    const searchInput = screen.getByPlaceholderText("Search bugs...");
    fireEvent.change(searchInput, { target: { value: "OPTIMIZER" } });

    await waitFor(() => {
      expect(screen.getByText("Bug 13364795")).toBeInTheDocument();
      expect(screen.queryByText("Bug 19396364")).not.toBeInTheDocument();
    });
  });

  it("search matches bug number", async () => {
    render(<BugList bugs={mockBugs} />);

    const searchInput = screen.getByPlaceholderText("Search bugs...");
    fireEvent.change(searchInput, { target: { value: "13364795" } });

    await waitFor(() => {
      expect(screen.getByText("Bug 13364795")).toBeInTheDocument();
      expect(screen.queryByText("Bug 19396364")).not.toBeInTheDocument();
      expect(screen.queryByText("Bug 17202207")).not.toBeInTheDocument();
    });
  });

  it("handles bugs without matches correctly", () => {
    render(<BugList bugs={mockBugs} />);

    // All bugs should be rendered even without matches
    expect(screen.getByText("Bug 13364795")).toBeInTheDocument();
    expect(screen.getByText("Bug 19396364")).toBeInTheDocument();
    expect(screen.getByText("Bug 17202207")).toBeInTheDocument();
  });

  it("associates matches with correct bugs", () => {
    render(
      <BugList bugs={mockBugs} matches={mockMatches} showConfidence={true} />
    );

    // Only the first bug should show confidence
    const bug1Card = screen.getByText("Bug 13364795").closest(".ant-card");
    expect(bug1Card).toHaveTextContent("85%");

    const bug2Card = screen.getByText("Bug 19396364").closest(".ant-card");
    expect(bug2Card).not.toHaveTextContent("85%");
  });
});
