import React from 'react'
import PageHead from '../components/PageHead.jsx'
import Button from '../components/Button.jsx'
import { Building2, FileText, Pill } from 'lucide-react'

const folders = [
  {
    key: 'prescriptions',
    label: 'Prescriptions',
    desc: 'Upload prescription images or PDFs. AI extracts medicine names and dosages.',
    icon: Pill,
    screen: 'documents',
  },
  {
    key: 'reports',
    label: 'Reports',
    desc: 'Create report folders (blood tests, diabetes, etc.) and upload diagnostics.',
    icon: FileText,
    screen: 'report-folders',
  },
]

export default function HospitalVault({ hospital, navigate, setVaultFolder }) {
  if (!hospital) {
    return (
      <div className="panel">
        <p className="muted">No hospital selected.</p>
        <Button onClick={() => navigate('hospitals')}>Back to hospitals</Button>
      </div>
    )
  }

  return (
    <React.Fragment>
      <PageHead
        eyebrow="Medical vault"
        title={hospital.name}
        desc={`${hospital.total_prescriptions + hospital.total_reports} documents stored`}
        icon={Building2}
        action={<Button variant="ghost" onClick={() => navigate('hospitals')}>All hospitals</Button>}
      />
      <div className="hospital-grid">
        {folders.map(folder => {
          const Icon = folder.icon
          const count =
            folder.key === 'prescriptions' ? hospital.total_prescriptions : hospital.total_reports
          return (
            <button
              key={folder.key}
              className="hospital-card selectable"
              onClick={() => {
                setVaultFolder(folder.key)
                navigate(folder.screen)
              }}
            >
              <div className="hospital-score">{count}</div>
              <span className="badge">
                <Icon size={15} />
                {folder.label}
              </span>
              <h3>{folder.label}</h3>
              <p>{folder.desc}</p>
            </button>
          )
        })}
      </div>
    </React.Fragment>
  )
}
