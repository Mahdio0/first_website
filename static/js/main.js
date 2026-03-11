document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("url-form");
    const urlInput = document.getElementById("video-url");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoading = submitBtn.querySelector(".btn-loading");
    const errorDiv = document.getElementById("error-message");
    const resultsDiv = document.getElementById("results");
    const summaryContent = document.getElementById("summary-content");
    const mindmapSvg = document.getElementById("mindmap-svg");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) return;

        // UI: loading state
        setLoading(true);
        hideError();
        resultsDiv.hidden = true;

        try {
            const response = await fetch("/api/summarize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            });

            const data = await response.json();

            if (!response.ok) {
                showError(data.error || "An unexpected error occurred.");
                return;
            }

            // Show summary
            summaryContent.textContent = data.summary;

            // Render mindmap
            renderMindmap(data.mindmap);

            resultsDiv.hidden = false;
        } catch {
            showError("Network error. Please check your connection and try again.");
        } finally {
            setLoading(false);
        }
    });

    function setLoading(loading) {
        submitBtn.disabled = loading;
        btnText.hidden = loading;
        btnLoading.hidden = !loading;
    }

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.hidden = false;
    }

    function hideError() {
        errorDiv.hidden = true;
        errorDiv.textContent = "";
    }

    /**
     * Convert the nested mindmap data object into Markdown headings
     * for markmap to render.
     */
    function mindmapDataToMarkdown(node, level) {
        if (level === undefined) level = 1;
        const prefix = "#".repeat(Math.min(level, 6));
        let md = prefix + " " + node.name + "\n";
        if (node.children) {
            for (const child of node.children) {
                if (child.children && child.children.length > 0) {
                    md += mindmapDataToMarkdown(child, level + 1);
                } else {
                    md += "- " + child.name + "\n";
                }
            }
        }
        return md;
    }

    /**
     * Render an interactive mindmap in the SVG element using markmap.
     */
    function renderMindmap(data) {
        // Clear previous content
        mindmapSvg.innerHTML = "";

        if (typeof markmap === "undefined" || !markmap.Markmap) {
            // Fallback: render a simple text tree if markmap isn't loaded
            renderFallbackTree(data);
            return;
        }

        const md = mindmapDataToMarkdown(data);

        const { Transformer } = markmap;
        const transformer = new Transformer();
        const { root } = transformer.transform(md);

        markmap.Markmap.create(mindmapSvg, {}, root);
    }

    /**
     * Fallback tree rendering when markmap CDN is unavailable.
     */
    function renderFallbackTree(data) {
        const container = document.getElementById("mindmap-container");
        const pre = document.createElement("pre");
        pre.style.padding = "1.5rem";
        pre.style.color = "#333";
        pre.style.fontSize = "0.9rem";
        pre.style.lineHeight = "1.6";
        pre.style.overflow = "auto";

        function buildText(node, indent) {
            let text = " ".repeat(indent) + (indent > 0 ? "├─ " : "") + node.name + "\n";
            if (node.children) {
                for (const child of node.children) {
                    text += buildText(child, indent + 3);
                }
            }
            return text;
        }

        pre.textContent = buildText(data, 0);
        // Replace SVG with pre for fallback
        mindmapSvg.style.display = "none";
        container.appendChild(pre);
    }
});
