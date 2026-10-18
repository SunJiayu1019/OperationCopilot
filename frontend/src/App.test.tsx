import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => cleanup());

describe("OperationCopilot workbench", () => {
  it("shows the task form and the four workflow stages", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /内容运营工作台/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/商品图片/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/内容目标/i)).toBeInTheDocument();
    expect(screen.getByText("素材分析")).toBeInTheDocument();
    expect(screen.getByText("文案生成")).toBeInTheDocument();
    expect(screen.getByText("内容审核")).toBeInTheDocument();
    expect(screen.getByText("自动改写")).toBeInTheDocument();
  });

  it("uploads the asset and submits a task to the API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/uploads")) {
        return new Response(JSON.stringify({ asset_id: "asset_test", filename: "snack.jpg" }), { status: 200 });
      }
      return new Response(JSON.stringify({
        id: "task_test",
        status: "completed",
        result: { product_summary: { name: "海盐坚果脆", category: "零食", selling_points: [] }, copy_variants: [], risks: [], rewritten: { title: "一口酥脆", body: "适合下午茶" } },
      }), { status: 201 });
    });
    render(<App />);
    fireEvent.change(screen.getByLabelText(/商品图片/i), { target: { files: [new File(["image"], "snack.jpg", { type: "image/jpeg" })] } });
    fireEvent.change(screen.getByLabelText(/内容目标/i), { target: { value: "突出下午茶" } });
    fireEvent.click(screen.getByRole("button", { name: /开始分析任务/i }));
    await waitFor(() => expect(screen.getByText("一口酥脆")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledTimes(2);
    fetchMock.mockRestore();
  });
});
