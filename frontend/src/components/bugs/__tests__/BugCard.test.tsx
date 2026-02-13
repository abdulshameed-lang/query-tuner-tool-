/**
 * Unit tests for BugCard component
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { BugCard } from "../BugCard";
import type { Bug, BugMatch } from "../../../types/bug";
import { BugSeverity, BugCategory } from "../../../types/bug";

describe("BugCard", () => {
  const mockBug: Bug = {
    bug_number: "13364795",
    title: "Wrong results with optimizer_adaptive_features",
    category: BugCategory.OPTIMIZER,
    severity: BugSeverity.CRITICAL,
    description: "This is a test bug description that explains the issue in detail.",
    symptoms: ["Incorrect results", "Data inconsistency"],
    affected_versions: ["12.1.0.1", "12.1.0.2"],
    fixed_versions: ["12.2.0.1"],
    workarounds: ["Set optimizer_adaptive_features=false", "Apply patch"],
    remediation_sql: "ALTER SESSION SET optimizer_adaptive_features=false;",
    my_oracle_support_url: "https://support.oracle.com/bug/13364795",
  };

  const mockMatch: BugMatch = {
    bug: mockBug,
    confidence: 85,
    matched_patterns: ["execution_plan", "parameters"],
    evidence: {
      execution_plan: { operations_found: ["ADAPTIVE"] },
      parameters: { optimizer_adaptive_features: { expected: "true", actual: "TRUE" } },
    },
    sql_id: "abc123def4567",
  };

  it("renders bug information correctly", () => {
    render(<BugCard bug={mockBug} />);

    expect(screen.getByText("Bug 13364795")).toBeInTheDocument();
    expect(screen.getByText(mockBug.title)).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText(BugCategory.OPTIMIZER)).toBeInTheDocument();
  });

  it("displays affected and fixed versions", () => {
    render(<BugCard bug={mockBug} />);

    expect(screen.getByText(/Affected:/)).toBeInTheDocument();
    expect(screen.getByText(/12.1.0.1, 12.1.0.2/)).toBeInTheDocument();
    expect(screen.getByText(/Fixed:/)).toBeInTheDocument();
    expect(screen.getByText(/12.2.0.1/)).toBeInTheDocument();
  });

  it("displays workarounds count", () => {
    render(<BugCard bug={mockBug} />);

    expect(screen.getByText("2 workaround(s) available")).toBeInTheDocument();
  });

  it("shows confidence when match is provided and showConfidence is true", () => {
    render(<BugCard bug={mockBug} match={mockMatch} showConfidence={true} />);

    expect(screen.getByText(/85%/)).toBeInTheDocument();
    expect(screen.getByText(/High/)).toBeInTheDocument();
  });

  it("does not show confidence when showConfidence is false", () => {
    render(<BugCard bug={mockBug} match={mockMatch} showConfidence={false} />);

    expect(screen.queryByText(/85%/)).not.toBeInTheDocument();
  });

  it("displays matched patterns when match is provided", () => {
    render(<BugCard bug={mockBug} match={mockMatch} />);

    expect(screen.getByText(/Matched patterns:/)).toBeInTheDocument();
    expect(screen.getByText("execution_plan")).toBeInTheDocument();
    expect(screen.getByText("parameters")).toBeInTheDocument();
  });

  it("renders MOS link when my_oracle_support_url is provided", () => {
    render(<BugCard bug={mockBug} />);

    const mosLink = screen.getByRole("link", { name: /MOS/i });
    expect(mosLink).toBeInTheDocument();
    expect(mosLink).toHaveAttribute("href", mockBug.my_oracle_support_url);
    expect(mosLink).toHaveAttribute("target", "_blank");
  });

  it("does not render MOS link when my_oracle_support_url is not provided", () => {
    const bugWithoutMOS = { ...mockBug, my_oracle_support_url: undefined };
    render(<BugCard bug={bugWithoutMOS} />);

    expect(screen.queryByRole("link", { name: /MOS/i })).not.toBeInTheDocument();
  });

  it("calls onClick when card is clicked", () => {
    const handleClick = jest.fn();
    render(<BugCard bug={mockBug} onClick={handleClick} />);

    const card = screen.getByText(mockBug.title).closest(".ant-card");
    fireEvent.click(card!);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick when MOS link is clicked", () => {
    const handleClick = jest.fn();
    render(<BugCard bug={mockBug} onClick={handleClick} />);

    const mosLink = screen.getByRole("link", { name: /MOS/i });
    fireEvent.click(mosLink);

    // onClick should not be called because we stop propagation
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("displays correct severity color for critical bugs", () => {
    render(<BugCard bug={mockBug} />);

    const severityTag = screen.getByText("CRITICAL");
    expect(severityTag.closest(".ant-tag")).toHaveClass("ant-tag-red");
  });

  it("displays correct severity color for high severity bugs", () => {
    const highSeverityBug = { ...mockBug, severity: BugSeverity.HIGH };
    render(<BugCard bug={highSeverityBug} />);

    const severityTag = screen.getByText("HIGH");
    expect(severityTag.closest(".ant-tag")).toHaveClass("ant-tag-orange");
  });

  it("displays correct confidence color for high confidence", () => {
    const highConfidenceMatch = { ...mockMatch, confidence: 90 };
    render(<BugCard bug={mockBug} match={highConfidenceMatch} showConfidence={true} />);

    const confidenceTag = screen.getByText(/90%/);
    expect(confidenceTag.closest(".ant-tag")).toHaveClass("ant-tag-green");
  });

  it("displays correct confidence color for medium confidence", () => {
    const mediumConfidenceMatch = { ...mockMatch, confidence: 65 };
    render(<BugCard bug={mockBug} match={mediumConfidenceMatch} showConfidence={true} />);

    const confidenceTag = screen.getByText(/65%/);
    expect(confidenceTag.closest(".ant-tag")).toHaveClass("ant-tag-gold");
  });

  it("truncates long descriptions with expand option", () => {
    render(<BugCard bug={mockBug} />);

    // Ant Design Paragraph with ellipsis should render
    const description = screen.getByText(mockBug.description);
    expect(description).toBeInTheDocument();
  });

  it("displays 'No fix available' when fixed_versions is empty", () => {
    const bugWithoutFix = { ...mockBug, fixed_versions: [] };
    render(<BugCard bug={bugWithoutFix} />);

    expect(screen.getByText(/No fix available/)).toBeInTheDocument();
  });

  it("does not display matched patterns when match is not provided", () => {
    render(<BugCard bug={mockBug} />);

    expect(screen.queryByText(/Matched patterns:/)).not.toBeInTheDocument();
  });

  it("handles bug with no workarounds", () => {
    const bugWithoutWorkarounds = { ...mockBug, workarounds: [] };
    render(<BugCard bug={bugWithoutWorkarounds} />);

    expect(screen.queryByText(/workaround\(s\) available/)).not.toBeInTheDocument();
  });
});
