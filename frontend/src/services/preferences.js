import { computed, readonly, ref } from 'vue'
import laraDarkThemeUrl from 'primevue/resources/themes/lara-dark-blue/theme.css?url'
import laraLightThemeUrl from 'primevue/resources/themes/lara-light-blue/theme.css?url'

const LANGUAGE_KEY = 'brats_language'
const THEME_KEY = 'brats_theme'

const messages = {
  en: {
    appName: 'Brats Segmentation App',
    language: 'Language',
    russian: 'RU',
    english: 'EN',
    theme: 'Theme',
    themeLight: 'Light',
    themeDark: 'Dark',
    themeSystem: 'System',
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    cancel: 'Cancel',
    logoutConfirmTitle: 'Confirm logout',
    logoutConfirmText: 'Do you really want to logout from your account?',
    loadScansError: 'Could not load scans. Check backend availability.',
    uploadFailed: 'Upload failed. Verify file names include modality keywords.',
    deleteScanFailed: 'Could not delete scan {caseId}.',
    realtimeDisconnected: 'Realtime scan updates are disconnected. The list may be stale.',
    uploadPanelTitle: 'Upload MRI modalities',
    automaticAssignment: 'Automatic assignment',
    automaticAssignmentCaption: 'Select 4 files in one action; filenames are mapped by keywords: t1, t1ce, t2, flair.',
    chooseFourFiles: 'Choose 4 files',
    requiredModalities: 'Required modalities',
    optionalTrueMask: 'Optional true mask',
    selected: 'Selected',
    missing: 'Missing',
    optional: 'Optional',
    replace: 'Replace',
    choose: 'Choose',
    createScan: 'Create scan',
    allModalitiesRequired: 'All 4 modalities are required for upload.',
    noFileSelected: 'No file selected',
    scansTitle: 'Created scans',
    searchByTitle: 'Search by title',
    sortAsc: 'A-Z',
    sortDesc: 'Z-A',
    title: 'Title',
    status: 'Status',
    actions: 'Actions',
    open: 'Open',
    delete: 'Delete',
    noScans: 'No scans yet.',
    dashboardSubtitle: 'Upload MRI modalities, track statuses, and open completed segmentations.',
    statusUploading: 'Uploading',
    statusProcessing: 'Processing',
    statusCompleted: 'Completed',
    statusFailed: 'Failed',
    statusUploaded: 'Uploaded',
    authLoginSubtitle: 'Enter your email and password to open your scans.',
    email: 'Email',
    password: 'Password',
    loginFailed: 'Could not login. Check your email and password.',
    createNewAccount: 'Create a new account',
    createAccount: 'Create account',
    registerSubtitle: 'Register to keep scans private and tied to your profile.',
    name: 'Name',
    alreadyHaveAccount: 'Already have an account? Login',
    registerFailed: 'Could not create account. The email may already be registered.',
    scanFallback: 'Scan {caseId}',
    scanTitlePlaceholder: 'Scan title',
    saveTitle: 'Save title',
    deleteScan: 'Delete scan',
    downloadJson: 'Export JSON',
    downloadCsv: 'Export CSV',
    chooseModality: 'MRI modality',
    downloadDicom: 'Export DICOM',
    sendDicomToOrthanc: 'Send to Orthanc',
    dicomConversionFailed: 'Could not convert the selected NIfTI modality to DICOM.',
    dicomOrthancSent: 'Sent {count} DICOM slices to Orthanc.',
    dicomOrthancFailed: 'Could not send DICOM slices to Orthanc.',
    dicomMetadata: 'DICOM metadata',
    dicomMetadataCaption: 'Optional fields saved with the scan and embedded into exported DICOM files.',
    dicomMetadataEmpty: 'Optional',
    saveDicomMetadata: 'Save DICOM metadata',
    dicomMetadataSaved: 'DICOM metadata saved.',
    dicomMetadataUpdateFailed: 'Could not update DICOM metadata.',
    dicomPatientName: 'Patient name',
    dicomPatientId: 'Patient ID',
    dicomPatientBirthDate: 'Patient birth date',
    dicomPatientSex: 'Patient sex',
    dicomPatientSexMale: 'Male',
    dicomPatientSexFemale: 'Female',
    dicomPatientSexOther: 'Other',
    dicomAccessionNumber: 'Accession number',
    dicomStudyId: 'Study ID',
    dicomStudyDate: 'Study date',
    dicomStudyDescription: 'Study description',
    dicomSeriesDescription: 'Series description',
    dicomInstitutionName: 'Institution name',
    dicomReferringPhysicianName: 'Referring physician',
    metricsLoadFailed: 'Could not load scan metrics. It may still be processing.',
    titleUpdateFailed: 'Could not update scan title.',
    currentScanDeleteFailed: 'Could not delete this scan.',
    scanSections: 'Scan sections',
    slicesSection: 'Slices',
    metricsSection: 'Metrics',
    metadataSection: 'Metadata',
    sectionSettings: 'Settings',
    dicomExportSettings: 'DICOM export',
    metricsExportSettings: 'Metrics export',
    metadataSettings: 'Metadata actions',
    metrics: 'Metrics',
    metric: 'Metric',
    value: 'Value',
    noMetrics: 'No metrics available.',
    segmentationSlice: 'Segmentation slice',
    sliceIndex: 'Slice index',
    quickAdjust: 'Quick adjust',
    overlay: 'Overlay',
    overlayMaskOnly: 'Mask only',
    loadSlice: 'Load slice',
    downloadPng: 'Download PNG',
    sliceLoadFailed: 'Unable to load slice image.',
    loadSlicePrompt: 'Load a slice image to preview segmentation mask.',
    maskSliceAlt: 'Segmentation mask slice',
    overlaySliceAlt: 'Segmentation mask slice covered with {modality} MRI scan'
  },
  ru: {
    appName: 'Brats Segmentation App',
    language: 'Язык',
    russian: 'RU',
    english: 'EN',
    theme: 'Тема',
    themeLight: 'Светлая',
    themeDark: 'Тёмная',
    themeSystem: 'Системная',
    login: 'Войти',
    register: 'Регистрация',
    logout: 'Выйти',
    cancel: 'Отмена',
    logoutConfirmTitle: 'Подтверждение выхода',
    logoutConfirmText: 'Вы действительно хотите выйти из аккаунта?',
    loadScansError: 'Не удалось загрузить сканы. Проверьте доступность бэкенда.',
    uploadFailed: 'Загрузка не удалась. Проверьте, что имена файлов содержат ключевые слова модальностей.',
    deleteScanFailed: 'Не удалось удалить скан {caseId}.',
    realtimeDisconnected: 'Соединение с обновлениями сканов разорвано. Список может быть устаревшим.',
    uploadPanelTitle: 'Загрузка МРТ-модальностей',
    automaticAssignment: 'Автоматическое сопоставление',
    automaticAssignmentCaption: 'Выберите 4 файла за одно действие; имена файлов сопоставляются по ключевым словам: t1, t1ce, t2, flair.',
    chooseFourFiles: 'Выбрать 4 файла',
    requiredModalities: 'Обязательные модальности',
    optionalTrueMask: 'Опциональная истинная маска',
    selected: 'Выбрано',
    missing: 'Нет файла',
    optional: 'Опционально',
    replace: 'Заменить',
    choose: 'Выбрать',
    createScan: 'Создать скан',
    allModalitiesRequired: 'Для загрузки нужны все 4 модальности.',
    noFileSelected: 'Файл не выбран',
    scansTitle: 'Созданные сканы',
    searchByTitle: 'Поиск по названию',
    sortAsc: 'А-Я',
    sortDesc: 'Я-А',
    title: 'Название',
    status: 'Статус',
    actions: 'Действия',
    open: 'Открыть',
    delete: 'Удалить',
    noScans: 'Сканов пока нет.',
    dashboardSubtitle: 'Загружайте модальности МРТ, отслеживайте статусы и открывайте готовые сегментации.',
    statusUploading: 'Загрузка',
    statusProcessing: 'Обработка',
    statusCompleted: 'Готово',
    statusFailed: 'Ошибка',
    statusUploaded: 'Загружено',
    authLoginSubtitle: 'Введите email и пароль, чтобы открыть свои сканы.',
    email: 'Email',
    password: 'Пароль',
    loginFailed: 'Не удалось войти. Проверьте email и пароль.',
    createNewAccount: 'Создать новый аккаунт',
    createAccount: 'Создать аккаунт',
    registerSubtitle: 'Зарегистрируйтесь, чтобы хранить сканы приватно и привязать их к профилю.',
    name: 'Имя',
    alreadyHaveAccount: 'Уже есть аккаунт? Войти',
    registerFailed: 'Не удалось создать аккаунт. Возможно, email уже зарегистрирован.',
    scanFallback: 'Скан {caseId}',
    scanTitlePlaceholder: 'Название скана',
    saveTitle: 'Сохранить',
    deleteScan: 'Удалить скан',
    downloadJson: 'Экспорт JSON',
    downloadCsv: 'Экспорт CSV',
    chooseModality: 'МРТ-модальность',
    downloadDicom: 'Экспорт DICOM',
    sendDicomToOrthanc: 'В Orthanc',
    dicomConversionFailed: 'Не удалось конвертировать выбранную NIfTI-модальность в DICOM.',
    dicomOrthancSent: 'В Orthanc отправлено срезов DICOM: {count}.',
    dicomOrthancFailed: 'Не удалось отправить DICOM-срезы в Orthanc.',
    dicomMetadata: 'Метаданные DICOM',
    dicomMetadataCaption: 'Необязательные поля сохраняются со сканом и добавляются в экспортируемые DICOM-файлы.',
    dicomMetadataEmpty: 'Необязательно',
    saveDicomMetadata: 'Сохранить метаданные DICOM',
    dicomMetadataSaved: 'Метаданные DICOM сохранены.',
    dicomMetadataUpdateFailed: 'Не удалось обновить метаданные DICOM.',
    dicomPatientName: 'Имя пациента',
    dicomPatientId: 'ID пациента',
    dicomPatientBirthDate: 'Дата рождения пациента',
    dicomPatientSex: 'Пол пациента',
    dicomPatientSexMale: 'Мужской',
    dicomPatientSexFemale: 'Женский',
    dicomPatientSexOther: 'Другое',
    dicomAccessionNumber: 'Номер обращения',
    dicomStudyId: 'ID исследования',
    dicomStudyDate: 'Дата исследования',
    dicomStudyDescription: 'Описание исследования',
    dicomSeriesDescription: 'Описание серии',
    dicomInstitutionName: 'Название учреждения',
    dicomReferringPhysicianName: 'Направивший врач',
    metricsLoadFailed: 'Не удалось загрузить метрики скана. Возможно, он ещё обрабатывается.',
    titleUpdateFailed: 'Не удалось обновить название скана.',
    currentScanDeleteFailed: 'Не удалось удалить этот скан.',
    scanSections: 'Разделы скана',
    slicesSection: 'Срезы',
    metricsSection: 'Метрики',
    metadataSection: 'Метаданные',
    sectionSettings: 'Настройки',
    dicomExportSettings: 'Экспорт DICOM',
    metricsExportSettings: 'Экспорт метрик',
    metadataSettings: 'Действия с метаданными',
    metrics: 'Метрики',
    metric: 'Метрика',
    value: 'Значение',
    noMetrics: 'Метрики недоступны.',
    segmentationSlice: 'Срез сегментации',
    sliceIndex: 'Номер среза',
    quickAdjust: 'Быстрая настройка',
    overlay: 'Наложение',
    overlayMaskOnly: 'Только маска',
    loadSlice: 'Загрузить срез',
    downloadPng: 'Скачать PNG',
    sliceLoadFailed: 'Не удалось загрузить изображение среза.',
    loadSlicePrompt: 'Загрузите срез, чтобы посмотреть маску сегментации.',
    maskSliceAlt: 'Срез маски сегментации',
    overlaySliceAlt: 'Срез маски сегментации поверх МРТ {modality}'
  }
}

const availableLanguages = ['en', 'ru']
const availableThemes = ['light', 'dark', 'system']

const storedLanguage = localStorage.getItem(LANGUAGE_KEY)
const language = ref(availableLanguages.includes(storedLanguage) ? storedLanguage : 'en')

const storedTheme = localStorage.getItem(THEME_KEY)
const theme = ref(availableThemes.includes(storedTheme) ? storedTheme : 'system')

const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
const systemTheme = ref(mediaQuery.matches ? 'dark' : 'light')
const resolvedTheme = computed(() => (theme.value === 'system' ? systemTheme.value : theme.value))

function formatMessage(template, params = {}) {
  return Object.entries(params).reduce((message, [key, value]) => message.replaceAll(`{${key}}`, value), template)
}

export function t(key, params = {}) {
  const template = messages[language.value]?.[key] ?? messages.en[key] ?? key
  return formatMessage(template, params)
}

function applyThemeClass() {
  const themeLinkId = 'primevue-theme'
  let themeLink = document.getElementById(themeLinkId)

  if (!themeLink) {
    themeLink = document.createElement('link')
    themeLink.id = themeLinkId
    themeLink.rel = 'stylesheet'
    document.head.appendChild(themeLink)
  }

  themeLink.href = resolvedTheme.value === 'dark' ? laraDarkThemeUrl : laraLightThemeUrl
  document.documentElement.dataset.theme = resolvedTheme.value
}

export function setLanguage(nextLanguage) {
  if (!availableLanguages.includes(nextLanguage)) return
  language.value = nextLanguage
  localStorage.setItem(LANGUAGE_KEY, nextLanguage)
}

export function setTheme(nextTheme) {
  if (!availableThemes.includes(nextTheme)) return
  theme.value = nextTheme
  localStorage.setItem(THEME_KEY, nextTheme)
  applyThemeClass()
}

export function initializePreferences() {
  document.body.style.margin = '0'
  applyThemeClass()

  mediaQuery.addEventListener('change', (event) => {
    systemTheme.value = event.matches ? 'dark' : 'light'
    applyThemeClass()
  })
}

export function usePreferences() {
  return {
    language: readonly(language),
    theme: readonly(theme),
    resolvedTheme,
    setLanguage,
    setTheme,
    t
  }
}
