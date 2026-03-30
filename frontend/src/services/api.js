const jsonHeaders = {
  Accept: 'application/json'
}

export async function fetchScans() {
  const response = await fetch('/scans', { headers: jsonHeaders })
  if (!response.ok) throw new Error('Failed to load scans')
  return response.json()
}

export async function uploadScan(filesByModality) {
  const formData = new FormData()
  Object.entries(filesByModality).forEach(([modality, file]) => {
    formData.append(modality, file)
  })

  const response = await fetch('/predict', {
    method: 'POST',
    body: formData
  })

  if (!response.ok) throw new Error('Failed to upload scan')
  return response.json()
}

export async function fetchMetrics(caseId) {
  const response = await fetch(`/scans/${caseId}/result/metrics`, { headers: jsonHeaders })
  if (!response.ok) throw new Error('Failed to load metrics')
  return response.json()
}

export async function downloadSlice(caseId, sliceIdx) {
  const response = await fetch(`/scans/${caseId}/result/images?slice_idx=${sliceIdx}`)
  if (!response.ok) throw new Error('Failed to download image')
  return response.blob()
}
