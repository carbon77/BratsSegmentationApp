import axios from 'axios'

const api = axios.create({
  headers: {
    Accept: 'application/json'
  }
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

export async function downloadSlice(caseId, sliceIdx) {
  const { data } = await api.get(`/scans/${caseId}/result/images?slice_idx=${sliceIdx}`, {
    responseType: 'blob'
  })
  return data
}

export async function deleteScan(caseId) {
  await api.delete(`/scans/${caseId}`)
}
