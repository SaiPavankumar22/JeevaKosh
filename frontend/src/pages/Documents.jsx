import React, { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import PageHead from '../components/PageHead.jsx'
import Button from '../components/Button.jsx'
import {
  deleteDocument,
  fetchDocuments,
  fetchOcrResult,
  fetchOcrStatus,
  fetchReportFolderDocuments,
  previewUrl,
  retryOcr,
  uploadDocument,
  uploadToReportFolder,
} from '../api'
import { FileText, Trash2, Upload } from 'lucide-react'

function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function OcrBadge({ status }) {
  const labels = {
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
  }
  return <span className="badge">{labels[status] ?? status}</span>
}

export default function Documents({
  hospital,
  vaultFolder,
  selectedReportFolder,
  navigate,
  setToast,
}) {
  const fileRef = useRef(null)
  const [uploadPct, setUploadPct] = useState(null)
  const [expandedId, setExpandedId] = useState(null)
  const [ocrData, setOcrData] = useState({})
  const qc = useQueryClient()

  const isReportFolder = vaultFolder === 'reports' && selectedReportFolder
  const title = isReportFolder
    ? selectedReportFolder.name
    : vaultFolder === 'prescriptions'
      ? 'Prescriptions'
      : 'Documents'

  const { data: docs = [], isPending } = useQuery({
    queryKey: ['documents', hospital?.id, vaultFolder, selectedReportFolder?.id],
    queryFn: () =>
      isReportFolder
        ? fetchReportFolderDocuments(hospital.id, selectedReportFolder.id)
        : fetchDocuments(hospital.id, vaultFolder),
    enabled: !!hospital?.id && !!vaultFolder && (vaultFolder !== 'reports' || !!selectedReportFolder),
    refetchInterval: 5000,
  })

  const uploadMutation = useMutation({
    mutationFn: file => {
      setUploadPct(0)
      return isReportFolder
        ? uploadToReportFolder(hospital.id, selectedReportFolder.id, file, setUploadPct)
        : uploadDocument(hospital.id, vaultFolder, file, setUploadPct)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', hospital.id] })
      qc.invalidateQueries({ queryKey: ['hospitals'] })
      qc.invalidateQueries({ queryKey: ['hospital', hospital.id] })
      qc.invalidateQueries({ queryKey: ['report-folders', hospital.id] })
      setUploadPct(null)
      setToast('Document uploaded')
      setTimeout(() => setToast(''), 3000)
    },
    onError: err => {
      setUploadPct(null)
      setToast(err.response?.data?.detail ?? 'Upload failed')
      setTimeout(() => setToast(''), 4000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', hospital.id] })
      qc.invalidateQueries({ queryKey: ['hospitals'] })
      setToast('Document deleted')
      setTimeout(() => setToast(''), 3000)
    },
  })

  async function toggleOcr(doc) {
    if (expandedId === doc.id) {
      setExpandedId(null)
      return
    }
    setExpandedId(doc.id)
    if (!ocrData[doc.id] && doc.ocr_status === 'completed') {
      const result = await fetchOcrResult(doc.id)
      setOcrData(prev => ({ ...prev, [doc.id]: result }))
    }
  }

  async function handleRetry(docId) {
    await retryOcr(docId)
    await fetchOcrStatus(docId)
    qc.invalidateQueries({ queryKey: ['documents', hospital.id] })
  }

  return (
    <React.Fragment>
      <PageHead
        eyebrow={hospital?.name}
        title={title}
        desc="Upload, view, and extract data from medical documents."
        icon={FileText}
        action={
          <Button
            variant="ghost"
            onClick={() => navigate(isReportFolder ? 'report-folders' : 'hospital-vault')}
          >
            Back
          </Button>
        }
      />

      <div className="panel" style={{ marginBottom: '1rem' }}>
        <input
          ref={fileRef}
          type="file"
          accept="image/*,.pdf"
          hidden
          onChange={e => {
            const file = e.target.files?.[0]
            if (file) uploadMutation.mutate(file)
            e.target.value = ''
          }}
        />
        <Button icon={Upload} onClick={() => fileRef.current?.click()} disabled={uploadMutation.isPending}>
          Upload document
        </Button>
        {uploadPct !== null && <p className="muted">Uploading… {uploadPct}%</p>}
      </div>

      {isPending ? (
        <p className="muted">Loading documents…</p>
      ) : docs.length === 0 ? (
        <div className="panel">
          <p className="muted">No documents yet. Upload your first file.</p>
        </div>
      ) : (
        <div className="timeline">
          {docs.map(doc => (
            <article className="timeline-card blue" key={doc.id}>
              <div>
                <h3>{doc.original_filename}</h3>
                <p className="muted">
                  {fmtSize(doc.file_size)} · {new Date(doc.upload_date).toLocaleDateString()}
                </p>
                <OcrBadge status={doc.ocr_status} />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <Button variant="ghost" onClick={() => window.open(previewUrl(doc.id), '_blank')}>
                  Preview
                </Button>
                <Button variant="ghost" onClick={() => toggleOcr(doc)}>
                  {expandedId === doc.id ? 'Hide OCR' : 'View OCR'}
                </Button>
                {doc.ocr_status === 'failed' && (
                  <Button variant="ghost" onClick={() => handleRetry(doc.id)}>
                    Retry OCR
                  </Button>
                )}
                <button
                  className="icon-btn"
                  onClick={() => {
                    if (confirm('Delete this document?')) deleteMutation.mutate(doc.id)
                  }}
                  aria-label="Delete"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              {expandedId === doc.id && (
                <pre className="report-content" style={{ marginTop: '1rem', overflow: 'auto' }}>
                  {doc.ocr_status === 'completed'
                    ? JSON.stringify(ocrData[doc.id] ?? doc.ocr_data ?? {}, null, 2)
                    : doc.ocr_status === 'failed'
                      ? doc.ocr_error ?? 'OCR failed'
                      : 'OCR in progress…'}
                </pre>
              )}
            </article>
          ))}
        </div>
      )}
    </React.Fragment>
  )
}
