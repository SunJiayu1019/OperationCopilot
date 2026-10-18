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

  it("submits a chat task, shows tool progress, and compares copy variants", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/uploads")) return new Response(JSON.stringify({ asset_id: "asset_chat", filename: "snack.jpg" }), { status: 200 });
      if (url.endsWith("/api/chat/tasks")) return new Response(JSON.stringify({ id: "chat_1", status: "pending", steps: [] }), { status: 202 });
      return new Response(JSON.stringify({
        id: "chat_1", status: "completed", steps: [{ tool: "analyze_image", status: "completed", message: "已完成" }],
        observations: { generate_copy: { copy_variants: [
          { title: "生活方式", body: "下班后的酥脆", tags: ["#下午茶"] },
          { title: "场景种草", body: "办公室分享", tags: ["#分享"] },
          { title: "信息清晰", body: "便携小包装", tags: ["#零食"] },
        ] }, review_copy: { reviews: [{ risks: [] }] } },
      }), { status: 200 });
    });
    render(<App />);
    fireEvent.change(screen.getByLabelText(/商品图片/i), { target: { files: [new File(["image"], "snack.jpg", { type: "image/jpeg" })] } });
    fireEvent.change(screen.getByLabelText(/内容目标/i), { target: { value: "生成下午茶文案" } });
    fireEvent.click(screen.getByRole("button", { name: /开始分析任务/i }));
    await waitFor(() => expect(screen.getByText("生活方式")).toBeInTheDocument());
    expect(screen.getByText("Agent 执行状态")).toBeInTheDocument();
    fetchMock.mockRestore();
  });
});
