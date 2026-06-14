import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Check,
  Clock,
  Copy,
  Download,
  ExternalLink,
  FileText,
  FolderOpen,
  Loader2,
  QrCode,
  Share2,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import PageHead from "../components/PageHead.jsx";
import Button from "../components/Button.jsx";
import { fetchAllDocuments, generatePortfolio, fetchMyShares, revokeShare } from "../api";

const EXPIRY_OPTIONS = [
  { value: 1,   label: "1 Hour",   sublabel: "Quick consult" },
  { value: 6,   label: "6 Hours",  sublabel: "Half-day" },
  { value: 24,  label: "24 Hours", sublabel: "Full day" },
  { value: 72,  label: "3 Days",   sublabel: "Short stay" },
  { value: 168, label: "7 Days",   sublabel: "Week follow-up" },
  { value: 720, label: "30 Days",  sublabel: "Long-term care" },
];

function fmt(dt) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function mimeIcon(mime) {
  if (mime?.includes("pdf"))   return "📄";
  if (mime?.includes("image")) return "🖼️";
  return "📁";
}

function groupByHospital(docs) {
  const map = {};
  for (const d of docs) {
    const key = d.hospital_name || "Unknown Hospital";
    if (!map[key]) map[key] = [];
    map[key].push(d);
  }
  return Object.entries(map).sort((a, b) => a[0].localeCompare(b[0]));
}

// ── Document section with hospital sub-groups ─────────────────────────────────
function DocTypeSection({ label, icon, docs, selectedDocs, toggleDoc, toggleGroup }) {
  const grouped = groupByHospital(docs);
  if (docs.length === 0) {
    return (
      <div className="sp-empty-small">
        No {label.toLowerCase()} uploaded yet.
      </div>
    );
  }
  return (
    <div className="sp-doc-type-section">
      <div className="sp-type-header">
        {icon}
        <span>{label}</span>
        <span className="sp-type-count">{docs.length} file{docs.length !== 1 ? "s" : ""}</span>
      </div>
      {grouped.map(([hospital, hdocs]) => {
        const ids = hdocs.map((d) => d.id);
        const allSel = ids.every((id) => selectedDocs.has(id));
        const someSel = ids.some((id) => selectedDocs.has(id));
        return (
          <div key={hospital} className="sp-doc-group">
            <button className="sp-group-header" onClick={() => toggleGroup(ids)}>
              <span className={`sp-checkbox ${allSel ? "checked" : someSel ? "partial" : ""}`}>
                {allSel ? <Check size={10} /> : someSel ? "–" : null}
              </span>
              <span className="sp-hospital-name">{hospital}</span>
              <span className="sp-doc-count">{hdocs.length}</span>
            </button>
            <div className="sp-doc-list">
              {hdocs.map((doc) => {
                const sel = selectedDocs.has(doc.id);
                return (
                  <button
                    key={doc.id}
                    className={`sp-doc-item ${sel ? "sp-doc-selected" : ""}`}
                    onClick={() => toggleDoc(doc.id)}
                  >
                    <span className={`sp-checkbox sm ${sel ? "checked" : ""}`}>
                      {sel ? <Check size={9} /> : null}
                    </span>
                    <span className="sp-doc-icon">{mimeIcon(doc.mime_type)}</span>
                    <span className="sp-doc-info">
                      <span className="sp-doc-name">{doc.original_filename}</span>
                      <span className="sp-doc-meta">
                        {doc.upload_date
                          ? new Date(doc.upload_date).toLocaleDateString("en-IN", {
                              day: "2-digit", month: "short", year: "numeric",
                            })
                          : "—"}
                        {doc.ocr_status === "done" && (
                          <span className="sp-ocr-badge">OCR ✓</span>
                        )}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function SharePortfolio() {
  const queryClient = useQueryClient();
  const [step, setStep] = useState("build");   // "build" | "result" | "history"
  const [selectedDocs, setSelectedDocs] = useState(new Set());
  const [expiryHours, setExpiryHours] = useState(24);
  const [portfolioTitle, setPortfolioTitle] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const { data: allDocs = [], isLoading: docsLoading } = useQuery({
    queryKey: ["portfolio-docs"],
    queryFn: fetchAllDocuments,
  });

  const { data: myShares = [], isLoading: sharesLoading } = useQuery({
    queryKey: ["my-shares"],
    queryFn: fetchMyShares,
    enabled: step === "history",
  });

  const generateMut = useMutation({
    mutationFn: () =>
      generatePortfolio([...selectedDocs], expiryHours, portfolioTitle.trim() || null),
    onSuccess: (data) => {
      setResult(data);
      setStep("result");
      queryClient.invalidateQueries({ queryKey: ["my-shares"] });
    },
  });

  const revokeMut = useMutation({
    mutationFn: (token) => revokeShare(token),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["my-shares"] }),
  });

  function toggleDoc(id) {
    setSelectedDocs((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleGroup(ids) {
    const allSelected = ids.every((id) => selectedDocs.has(id));
    setSelectedDocs((prev) => {
      const next = new Set(prev);
      if (allSelected) ids.forEach((id) => next.delete(id));
      else ids.forEach((id) => next.add(id));
      return next;
    });
  }

  function copyLink() {
    if (!result?.share_url) return;
    navigator.clipboard.writeText(result.share_url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  }

  function downloadQr() {
    if (!result?.qr_code_base64) return;
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${result.qr_code_base64}`;
    a.download = `portfolio-qr-${result.token?.slice(0, 8)}.png`;
    a.click();
  }

  function reset() {
    setStep("build");
    setResult(null);
    setSelectedDocs(new Set());
    setCopied(false);
  }

  const prescriptions = allDocs.filter((d) => d.folder === "prescriptions");
  const reports       = allDocs.filter((d) => d.folder === "reports");
  const expiryOption  = EXPIRY_OPTIONS.find((o) => o.value === expiryHours);

  // ── RESULT SCREEN ─────────────────────────────────────────────────────────
  if (step === "result" && result) {
    return (
      <div className="sp-page">
        <PageHead icon={Share2} title="Portfolio Ready" desc="Share this secure link or QR code with your doctor" />

        <div className="sp-result-grid">
          {/* QR panel */}
          <div className="sp-qr-panel">
            <p className="sp-qr-label"><QrCode size={15} /> Scan QR Code</p>
            {result.qr_code_base64 ? (
              <img
                src={`data:image/png;base64,${result.qr_code_base64}`}
                alt="Portfolio QR Code"
                className="sp-qr-img"
              />
            ) : (
              <div className="sp-qr-placeholder">QR unavailable</div>
            )}
            <button className="sp-qr-download" onClick={downloadQr}>
              <Download size={13} /> Download QR PNG
            </button>
          </div>

          {/* Link panel */}
          <div className="sp-link-panel">
            <div className="sp-link-meta">
              <ShieldCheck size={20} className="sp-shield" />
              <div>
                <p className="sp-link-title">{result.title || "Medical Portfolio"}</p>
                <p className="sp-link-sub">Expires: {fmt(result.expires_at)} ({result.expires_label})</p>
              </div>
            </div>

            <div className="sp-link-box">
              <a href={result.share_url} target="_blank" rel="noopener noreferrer" className="sp-link-text">
                {result.share_url}
              </a>
              <button className="sp-copy-btn" onClick={copyLink}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>

            <div className="sp-result-stats">
              <span><FileText size={13} /> Profile data included</span>
              <span><FolderOpen size={13} /> {result.document_count} document{result.document_count !== 1 ? "s" : ""}</span>
              <span><Clock size={13} /> Valid {result.expires_label}</span>
            </div>

            <div className="sp-result-note">
              <AlertTriangle size={14} />
              Share only with trusted medical professionals. This link gives read-only access to your selected data.
            </div>

            <div className="sp-result-actions">
              <Button onClick={reset}>Generate Another</Button>
              <button className="sp-history-btn" onClick={() => setStep("history")}>
                View All Shares
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── HISTORY SCREEN ────────────────────────────────────────────────────────
  if (step === "history") {
    return (
      <div className="sp-page">
        <PageHead icon={Clock} title="Active Portfolio Shares" desc="Manage your shared portfolios — revoke access anytime" />

        <div className="sp-history-top">
          <Button onClick={() => setStep("build")}><Share2 size={14} /> New Share</Button>
        </div>

        {sharesLoading ? (
          <div className="sp-loading"><Loader2 size={20} className="sp-spin" /> Loading shares…</div>
        ) : myShares.length === 0 ? (
          <div className="sp-empty">
            <QrCode size={38} />
            <p>No portfolio shares yet.</p>
            <button className="sp-link-btn" onClick={() => setStep("build")}>Create your first share →</button>
          </div>
        ) : (
          <div className="sp-history-list">
            {myShares.map((share) => {
              const inactive = share.is_expired || share.is_revoked;
              return (
                <div key={share.token} className={`sp-share-card ${inactive ? "sp-share-inactive" : ""}`}>
                  <div className="sp-share-head">
                    <div>
                      <p className="sp-share-title">{share.title || "Medical Portfolio"}</p>
                      <p className="sp-share-meta">Created: {fmt(share.created_at)}</p>
                    </div>
                    <span className={`sp-badge ${share.is_revoked ? "sp-badge-revoked" : share.is_expired ? "sp-badge-expired" : "sp-badge-active"}`}>
                      {share.is_revoked ? "Revoked" : share.is_expired ? "Expired" : "Active"}
                    </span>
                  </div>
                  <div className="sp-share-details">
                    <span><FolderOpen size={13} /> {share.document_count} docs</span>
                    <span><Clock size={13} /> Expires: {fmt(share.expires_at)}</span>
                  </div>
                  {!inactive && (
                    <div className="sp-share-actions">
                      <a href={share.share_url} target="_blank" rel="noopener noreferrer" className="sp-open-link">
                        <ExternalLink size={13} /> Open PDF
                      </a>
                      <button className="sp-revoke-btn" onClick={() => revokeMut.mutate(share.token)} disabled={revokeMut.isPending}>
                        <Trash2 size={13} /> Revoke
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // ── BUILD SCREEN ──────────────────────────────────────────────────────────
  return (
    <div className="sp-page">
      <PageHead icon={Share2} title="Share Medical Portfolio" desc="Generate a secure, time-limited PDF to share with your doctor" />

      <div className="sp-build-layout">
        {/* LEFT — Document selection */}
        <div className="sp-left-panel">
          {/* Profile (always included) */}
          <div className="sp-section-head">
            <ShieldCheck size={15} className="sp-icon-teal" />
            <span>Profile Summary</span>
            <span className="sp-always-tag">Always included</span>
          </div>
          <div className="sp-profile-preview">
            <FileText size={13} />
            Personal info · Emergency contact · Allergies · Medications · Conditions · Surgeries
          </div>

          {/* Documents */}
          <div className="sp-section-head" style={{ marginTop: "1.2rem" }}>
            <FolderOpen size={15} className="sp-icon-teal" />
            <span>Medical Documents</span>
            <span className="sp-selected-count">
              {selectedDocs.size > 0 ? `${selectedDocs.size} selected` : "optional"}
            </span>
          </div>

          {docsLoading ? (
            <div className="sp-loading"><Loader2 size={18} className="sp-spin" /> Loading documents…</div>
          ) : allDocs.length === 0 ? (
            <div className="sp-empty-small">No documents uploaded yet. Your portfolio will include only your profile data.</div>
          ) : (
            <div className="sp-doc-groups">
              <DocTypeSection
                label="Prescriptions"
                icon={<span className="sp-type-emoji">💊</span>}
                docs={prescriptions}
                selectedDocs={selectedDocs}
                toggleDoc={toggleDoc}
                toggleGroup={toggleGroup}
              />
              <DocTypeSection
                label="Reports"
                icon={<span className="sp-type-emoji">🔬</span>}
                docs={reports}
                selectedDocs={selectedDocs}
                toggleDoc={toggleDoc}
                toggleGroup={toggleGroup}
              />
            </div>
          )}
        </div>

        {/* RIGHT — Options + Generate */}
        <div className="sp-right-panel">
          <div className="sp-option-section">
            <label className="sp-option-label">Portfolio Title <span className="sp-optional">(optional)</span></label>
            <input
              className="sp-text-input"
              placeholder="e.g. Cardiology Consult – Dr. Sharma"
              value={portfolioTitle}
              maxLength={120}
              onChange={(e) => setPortfolioTitle(e.target.value)}
            />
          </div>

          <div className="sp-option-section">
            <label className="sp-option-label"><Clock size={13} /> Access Duration</label>
            <div className="sp-expiry-grid">
              {EXPIRY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  className={`sp-expiry-btn ${expiryHours === opt.value ? "sp-expiry-active" : ""}`}
                  onClick={() => setExpiryHours(opt.value)}
                >
                  <span className="sp-expiry-label">{opt.label}</span>
                  <span className="sp-expiry-sub">{opt.sublabel}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="sp-summary-box">
            <p className="sp-summary-title">Portfolio will include:</p>
            <ul className="sp-summary-list">
              <li><Check size={12} /> Full profile (medications, allergies, surgeries, conditions)</li>
              {selectedDocs.size > 0 && (
                <li><Check size={12} /> {selectedDocs.size} medical document{selectedDocs.size !== 1 ? "s" : ""} (with image previews)</li>
              )}
              <li><Clock size={12} /> Expires in {expiryOption?.label}</li>
            </ul>
          </div>

          {generateMut.isError && (
            <div className="sp-error-msg">
              <AlertTriangle size={14} />
              {generateMut.error?.response?.data?.detail ?? generateMut.error?.message ?? "Generation failed."}
            </div>
          )}

          <Button
            onClick={() => generateMut.mutate()}
            disabled={generateMut.isPending}
            style={{ width: "100%", justifyContent: "center" }}
          >
            {generateMut.isPending ? (
              <><Loader2 size={14} className="sp-spin" /> Generating PDF…</>
            ) : (
              <><Share2 size={14} /> Generate & Share</>
            )}
          </Button>

          <button className="sp-history-btn" onClick={() => { setStep("history"); queryClient.invalidateQueries({ queryKey: ["my-shares"] }); }}>
            View my active shares →
          </button>
        </div>
      </div>
    </div>
  );
}
