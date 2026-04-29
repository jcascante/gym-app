import { describe, expect, it } from "vitest";
import { formatDuration, formatHrRange, formatLoad } from "@/lib/utils";

describe("formatLoad", () => {
  it("formats kg by default", () => {
    expect(formatLoad(120)).toBe("120 kg");
  });

  it("formats lb when specified", () => {
    expect(formatLoad(100, "lb")).toBe("220.5 lb");
  });
});

describe("formatHrRange", () => {
  it("formats heart rate range", () => {
    expect(formatHrRange([150, 163])).toBe("150–163 bpm");
  });
});

describe("formatDuration", () => {
  it("formats minutes under 60", () => {
    expect(formatDuration(35)).toBe("35 min");
  });

  it("formats hours", () => {
    expect(formatDuration(60)).toBe("1h");
  });

  it("formats hours and minutes", () => {
    expect(formatDuration(90)).toBe("1h 30min");
  });
});
