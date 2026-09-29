"use client";

import { ChangeEvent, DragEvent, FormEvent, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check, Download, FileText, RotateCcw, UploadCloud, X } from "lucide-react";
import { apiUrl, Tool } from "@/lib/tools";

const maxSize = 50 * 1024 * 1024;
type Result = { download_id: string; filename: string; size: number; mime_type: string };
const formatSize = (bytes: number) => bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

export function Converter({ tool }: { tool: Tool }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [pages, setPages] = useState("");
  const [rotation, setRotation] = useState("90");
  const [sheet, setSheet] = useState("");
  const [pageCount, setPageCount] = useState<number | null>(null);
  const [inspecting, setInspecting] = useState(false);

  async function inspect(selected: File) {
    setInspecting(true);
    try {
      const form = new FormData(); form.append("file", selected);
      const response = await fetch(`${apiUrl()}/api/pdf/inspect`, { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not read this PDF.");
      setPageCount(data.page_count);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not read this PDF."); }
    finally { setInspecting(false); }
  }

  function choose(selected?: File) {
    setError(""); setResult(null); setPageCount(null); setPages("");
    if (!selected) return;
    const allowed = tool.accept.split(",").some(ext => selected.name.toLowerCase().endsWith(ext));
    if (!allowed) { setFile(null); setError("Unsupported file format for this tool."); return; }
    if (selected.size > maxSize) { setFile(null); setError("File exceeds the 50 MB limit."); return; }
    if (selected.size === 0) { setFile(null); setError("Choose a non-empty file."); return; }
    setFile(selected);
    if (tool.slug.startsWith("pdf-") && ["pdf-split", "pdf-rotate", "pdf-extract", "pdf-reorder"].includes(tool.slug)) void inspect(selected);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); setDragging(false);
    if (event.dataTransfer.files.length !== 1) { setError("Choose one file at a time."); return; }
    choose(event.dataTransfer.files[0]);
  }
  function onInput(event: ChangeEvent<HTMLInputElement>) { choose(event.target.files?.[0]); event.target.value = ""; }
  function reset() { setFile(null); setResult(null); setError(""); setPages(""); setSheet(""); setPageCount(null); }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || busy) return;
    setError(""); setBusy(true);
    const options: Record<string, string> = {};
    if (tool.option === "pages" || tool.option === "reorder") options.pages = pages.trim();
    if (tool.option === "rotate") { options.pages = pages.trim() || "all"; options.rotation = rotation; }
    if (tool.option === "sheet") options.sheet = sheet.trim();
    const form = new FormData(); form.append("file", file); form.append("options", JSON.stringify(options));
    const path = tool.slug.startsWith("pdf-") && ["pdf-split", "pdf-rotate", "pdf-extract", "pdf-reorder"].includes(tool.slug)
      ? `/api/pdf/${tool.slug.slice(4)}` : `/api/convert/${tool.slug}`;
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 150000);
      try {
        const response = await fetch(`${apiUrl()}${path}`, { method: "POST", body: form, signal: controller.signal });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Conversion could not be completed.");
        setResult(data as Result);
      } finally { clearTimeout(timer); }
    } catch (cause) {
      setError(cause instanceof Error && cause.name === "AbortError" ? "The conversion took too long." : cause instanceof TypeError ? "The server is temporarily unavailable." : cause instanceof Error ? cause.message : "Conversion could not be completed.");
    } finally { setBusy(false); }
  }

  return <div className="container converter-page"><Link href="/#tools" className="back-link"><ArrowLeft size={16} /> All tools</Link><div className="converter-heading"><span className="section-kicker">{tool.category.toUpperCase()}</span><h1>{tool.title}</h1><p>{tool.description}</p></div>
    <div className="converter-layout"><form onSubmit={submit} className="converter-card"><div className="card-heading"><h2>Upload your file</h2><span>{tool.input} <span aria-hidden="true">→</span> {tool.output}</span></div>
      {!result ? <><input ref={input} type="file" accept={tool.accept} multiple={false} onChange={onInput} className="sr-only" aria-label={`Choose a ${tool.input} file`} />
        {!file ? <div className={`drop-zone ${dragging ? "is-dragging" : ""}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <span className="upload-icon"><UploadCloud size={27} strokeWidth={1.7} /></span><strong>Drag and drop your file here</strong><p>or select one from your device</p><button type="button" className="button button-secondary" onClick={() => input.current?.click()}>Browse files</button><small>Accepted: {tool.input}</small>
        </div> : <div className="selected-file"><span className="selected-icon"><FileText size={21} /></span><div><strong>{file.name}</strong><span>{formatSize(file.size)}</span></div><button type="button" onClick={() => input.current?.click()} disabled={busy} aria-label="Replace file">Replace</button><button type="button" className="icon-button" onClick={() => setFile(null)} disabled={busy} aria-label="Remove file"><X size={18} /></button></div>}
        {file && <div className="options">
          {pageCount !== null && <p className="page-count">This PDF has {pageCount} {pageCount === 1 ? "page" : "pages"}.</p>}
          {inspecting && <p className="page-count">Reading page count…</p>}
          {tool.option === "pages" && <label>{tool.slug === "pdf-split" ? "Page range" : "Pages to extract"}<input required value={pages} onChange={event => setPages(event.target.value)} placeholder={tool.slug === "pdf-split" ? "1-3" : "1-3,6,8"} /><small>{tool.slug === "pdf-split" ? "Enter one continuous range, such as 1-3." : "Use page numbers or ranges, such as 1-3,6,8."}</small></label>}
          {tool.option === "reorder" && <label>New page order<input required value={pages} onChange={event => setPages(event.target.value)} placeholder={pageCount ? Array.from({ length: Math.min(pageCount, 4) }, (_, i) => i + 1).reverse().join(",") : "3,1,2,4"} /><small>List every page once. Duplicates are not allowed.</small></label>}
          {tool.option === "rotate" && <><label>Rotation<select value={rotation} onChange={event => setRotation(event.target.value)}><option value="90">90° clockwise</option><option value="180">180°</option><option value="270">270° clockwise</option></select></label><label>Pages to rotate<input value={pages} onChange={event => setPages(event.target.value)} placeholder="All pages" /><small>Leave blank for all pages, or enter 1-3,6.</small></label></>}
          {tool.option === "sheet" && <label>Worksheet name <span className="optional">(optional)</span><input value={sheet} onChange={event => setSheet(event.target.value)} placeholder="First worksheet" /><small>Leave blank to export the first worksheet.</small></label>}
        </div>}
        {error && <div className="error-message" role="alert">{error}</div>}
        <button className="button button-primary convert-button" type="submit" disabled={!file || busy || inspecting}>{busy ? <><span className="spinner" /> Converting…</> : "Convert file"}</button>
      </> : <div className="result-card" role="status"><span className="success-icon"><Check size={25} /></span><h3>Conversion complete</h3><p>Your file is ready to download.</p><div className="result-file"><FileText size={21} /><span><strong>{result.filename}</strong><small>{formatSize(result.size)}</small></span></div><a className="button button-primary" href={`${apiUrl()}/api/download/${result.download_id}`} download={result.filename}><Download size={17} /> Download file</a><button type="button" className="button button-quiet" onClick={reset}><RotateCcw size={16} /> Convert another file</button></div>}
    </form><aside className="privacy-card"><h2>Good to know</h2><div><strong>One file at a time</strong><p>Each conversion handles a single upload.</p></div><div><strong>Maximum file size: 50 MB</strong><p>Large files are rejected before processing.</p></div><div><strong>Temporary processing</strong><p>Files are temporarily processed and automatically deleted within 5 minutes.</p></div></aside></div>
  </div>;
}
