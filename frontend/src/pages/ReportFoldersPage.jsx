import React, { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import PageHead from '../components/PageHead.jsx'
import Button from '../components/Button.jsx'
import { createReportFolder, deleteReportFolder, fetchReportFolders } from '../api'
import { FileText, FolderPlus, Trash2 } from 'lucide-react'

export default function ReportFoldersPage({
  hospital,
  navigate,
  setSelectedReportFolder,
}) {
  const [name, setName] = useState('')
  const [showForm, setShowForm] = useState(false)
  const qc = useQueryClient()

  const { data: folders = [], isPending } = useQuery({
    queryKey: ['report-folders', hospital?.id],
    queryFn: () => fetchReportFolders(hospital.id),
    enabled: !!hospital?.id,
  })

  const createMutation = useMutation({
    mutationFn: () => createReportFolder(hospital.id, name.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['report-folders', hospital.id] })
      setName('')
      setShowForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: rfId => deleteReportFolder(hospital.id, rfId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['report-folders', hospital.id] }),
  })

  return (
    <React.Fragment>
      <PageHead
        eyebrow={hospital?.name}
        title="Report folders"
        desc="Organize lab reports and diagnostics by category."
        icon={FileText}
        action={
          <Button variant="ghost" onClick={() => navigate('hospital-vault')}>
            Back
          </Button>
        }
      />

      <div className="panel" style={{ marginBottom: '1rem' }}>
        <Button icon={FolderPlus} onClick={() => setShowForm(v => !v)}>
          New folder
        </Button>
        {showForm && (
          <form
            className="form-grid"
            style={{ marginTop: '1rem' }}
            onSubmit={e => {
              e.preventDefault()
              if (name.trim()) createMutation.mutate()
            }}
          >
            <label className="field full">
              <span>Folder name</span>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g. Blood Test"
                required
              />
            </label>
            <Button type="submit" disabled={createMutation.isPending}>
              Create
            </Button>
          </form>
        )}
      </div>

      {isPending ? (
        <p className="muted">Loading folders…</p>
      ) : folders.length === 0 ? (
        <div className="panel">
          <p className="muted">No report folders yet. Create one to start uploading.</p>
        </div>
      ) : (
        <div className="hospital-grid">
          {folders.map(folder => (
            <article className="hospital-card" key={folder.id}>
              <button
                className="selectable"
                style={{ textAlign: 'left', width: '100%' }}
                onClick={() => {
                  setSelectedReportFolder(folder)
                  navigate('documents')
                }}
              >
                <div className="hospital-score">{folder.total_documents}</div>
                <h3>{folder.name}</h3>
                <p className="muted">{folder.total_documents} document(s)</p>
              </button>
              <button
                className="icon-btn"
                style={{ marginTop: '0.5rem' }}
                onClick={() => {
                  if (confirm(`Delete folder "${folder.name}"?`)) deleteMutation.mutate(folder.id)
                }}
                aria-label="Delete folder"
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      )}
    </React.Fragment>
  )
}
