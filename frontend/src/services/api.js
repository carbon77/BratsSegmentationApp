import axios from 'axios'

const api = axios.create({
  headers: {
    Accept: 'application/json'
  },
  baseURL: '/api'
})

export async function fetchScans() {
  const { data } = await api.get('/scans')
  return data
}

export async function uploadScan(filesByModality) {
  const formData = new FormData()
  Object.entries(filesByModality).forEach(([modality, file]) => {
    if (file) {
      formData.append(modality, file)
    }
  })

  const { data } = await api.post('/predict', formData)
  return data
}

export async function fetchMetrics(caseId) {
  const { data } = await api.get(`/scans/${caseId}/result/metrics`)
  return data
}

export async function patchScanTitle(caseId, title) {
  await api.patch(`/scans/${caseId}`, { title })
}

export async function downloadSlice(caseId, sliceIdx, overlayModality = null) {
  const params = { slice_idx: sliceIdx }
  if (overlayModality) {
    params.overlay_modality = overlayModality
  }

  const { data } = await api.get(`/scans/${caseId}/result/images`, {
    params,
    responseType: 'blob'
  })
  return data
}

export async function deleteScan(caseId) {
  await api.delete(`/scans/${caseId}`)
}
