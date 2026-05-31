import axios from 'axios'

const TOKEN_KEY = 'brats_auth_token'
const USER_KEY = 'brats_auth_user'

const api = axios.create({
  headers: {
    Accept: 'application/json'
  },
  baseURL: '/api'
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser() {
  const rawUser = localStorage.getItem(USER_KEY)
  if (!rawUser) return null

  try {
    return JSON.parse(rawUser)
  } catch {
    return null
  }
}

export function isAuthenticated() {
  return Boolean(getToken())
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

function storeAuth(payload) {
  localStorage.setItem(TOKEN_KEY, payload.access_token)
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
  window.dispatchEvent(new Event('auth-changed'))
  return payload.user
}

export async function registerAccount(credentials) {
  const { data } = await api.post('/auth/register', credentials)
  return storeAuth(data)
}

export async function login(credentials) {
  const { data } = await api.post('/auth/login', credentials)
  return storeAuth(data)
}

export async function fetchCurrentUser() {
  const { data } = await api.get('/auth/me')
  localStorage.setItem(USER_KEY, JSON.stringify(data))
  return data
}

export function logout() {
  clearAuth()
  window.dispatchEvent(new Event('auth-changed'))
}

export async function fetchScans() {
  const { data } = await api.get('/scans')
  return data
}

export async function fetchScan(caseId) {
  const { data } = await api.get(`/scans/${caseId}`)
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

export async function updateDicomMetadata(caseId, dicomMetadata) {
  await api.patch(`/scans/${caseId}`, { dicom_metadata: dicomMetadata })
}

export async function downloadSlice(caseId, sliceIdx, overlayModality = null, includeMask = true) {
  const params = { slice_idx: sliceIdx, include_mask: includeMask }
  if (overlayModality) {
    params.overlay_modality = overlayModality
  }

  const { data } = await api.get(`/scans/${caseId}/result/images`, {
    params,
    responseType: 'blob'
  })
  return data
}

export async function downloadDicomArchive(caseId, modality) {
  const { data } = await api.get(`/scans/${caseId}/dicom`, {
    params: { modality },
    responseType: 'blob'
  })
  return data
}

export async function sendDicomToOrthanc(caseId, modality) {
  const { data } = await api.post(`/scans/${caseId}/dicom/orthanc`, null, {
    params: { modality }
  })
  return data
}

export async function deleteScan(caseId) {
  await api.delete(`/scans/${caseId}`)
}

export function subscribeToScans(onScans, onError) {
  const token = getToken()
  const params = token ? `?token=${encodeURIComponent(token)}` : ''
  const eventSource = new EventSource(`/api/scans/events${params}`)

  eventSource.addEventListener('scans', (event) => {
    onScans(JSON.parse(event.data))
  })

  if (onError) {
    eventSource.onerror = onError
  }

  return () => eventSource.close()
}
