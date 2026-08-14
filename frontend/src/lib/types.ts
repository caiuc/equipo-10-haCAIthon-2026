/** Contratos que devuelve la API. Reflejan los modelos Pydantic del backend. */

export type Regimen = 'GES' | 'NO_GES'
export type Stage = 'SOSPECHA' | 'DIAGNOSTICO' | 'TRATAMIENTO' | 'SEGUIMIENTO'
export type PatientType = 'AMBULATORIO' | 'HOSPITALARIO'
export type Severity = 'ALTA' | 'MEDIA' | 'BAJA'
export type PriorityLevel = 'CRITICA' | 'ALTA_PRIORIDAD' | 'MEDIA_PRIORIDAD' | 'ESTANDAR'
export type CivilRegistryStatus = 'ALIVE' | 'DECEASED' | 'PENDING_VERIFICATION'

export type WaitlistOrder =
  | 'priority_desc'
  | 'priority_asc'
  | 'expiration_asc'
  | 'expiration_desc'
  | 'days_desc'
  | 'days_asc'

export interface PatientFlags {
  is_oncologic: boolean
  is_ancient_patient: boolean
  incomplete_info: boolean
  ges_delayed: boolean
  civil_registry_status: CivilRegistryStatus
}

export interface ScoreBreakdown {
  time_waiting_score: number
  clinical_severity_score: number
  oncologic_risk_score: number
  diagnostic_validity_penalty: number
}

export interface ScoreMetadata {
  days_waiting: number
  regional_median_days: number
  regional_p75_days: number
  exams_expired: boolean
  last_evaluation_date: string | null
  calculated_at: string
}

export interface PatientScore {
  patient_id: string
  national_id: string
  regimen: Regimen
  stage: Stage
  specialty: string
  health_service_id: string
  total_score: number
  priority_level: PriorityLevel
  flags: PatientFlags
  breakdown?: ScoreBreakdown
  metadata: ScoreMetadata
}

export interface WaitlistItem {
  rank: number
  patient_id: string
  national_id: string
  full_name: string
  specialty: string
  specialty_label: string
  stage: Stage
  regimen: Regimen
  patient_type: PatientType
  health_service_id: string
  health_service_label: string
  ges_expiration_date: string | null
  days_waiting: number
  regional_median_days: number
  regional_p75_days: number
  priority_score: number
  priority_level: PriorityLevel
  flags: PatientFlags
}

export interface WaitlistResponse {
  total_records: number
  page: number
  limit: number
  total_pages: number
  data: WaitlistItem[]
}

export interface PatientDetail {
  patient_id: string
  national_id: string
  national_id_formatted: string
  full_name: string
  birth_date: string | null
  age: number | null
  regimen: Regimen
  ges_expiration_date: string | null
  patient_type: PatientType
  specialty: string
  specialty_label: string
  stage: Stage
  health_service_id: string
  health_service_label: string
  diagnosis: string
  entry_date: string
  days_waiting: number
  last_exams_date: string | null
  is_oncologic: boolean
  clinical_severity: Severity
  staging: string | null
  contact_phone: string | null
  civil_registry_status: CivilRegistryStatus
  date_of_death: string | null
  source_adapter: string
  score: PatientScore
}

export interface CatalogEntry {
  value: string
  label: string
}

export interface SpecialtyCatalogEntry extends CatalogEntry {
  median_days: number
  p75_days: number
  is_oncologic: boolean
}

export interface Catalog {
  specialties: SpecialtyCatalogEntry[]
  health_services: CatalogEntry[]
  stages: CatalogEntry[]
  patient_types: CatalogEntry[]
  severities: CatalogEntry[]
  regimens: CatalogEntry[]
  orders: CatalogEntry[]
}

export interface SpecialtyStat {
  specialty: string
  label: string
  patients: number
  median_days_waiting: number
}

export interface Stats {
  total_waiting: number
  oncologic: number
  ges_total: number
  ges_delayed: number
  ancient_patients: number
  incomplete_info: number
  pending_civil_registry: number
  median_days_waiting: number
  p75_days_waiting: number
  average_score: number
  top_specialties: SpecialtyStat[]
}

export interface PurgedPatient {
  patient_id: string
  full_name: string
  date_of_death: string | null
  purged_reason: string
}

export interface SyncResult {
  processed_records: number
  alive_records: number
  purged_deceased_records: number
  purged_patients: PurgedPatient[]
  synced_at: string
}

/** Filtros de la lista de espera, tal como viajan en la query string. */
export interface WaitlistFilters {
  specialty: string
  patient_type: string
  regimen: string
  stage: string
  health_service: string
  q: string
  order: WaitlistOrder
  page: number
  limit: number
}

/** Campos editables desde "Actualizar estado". */
export interface ClinicalStatusUpdate {
  regimen?: Regimen
  fecha_expiracion_ges?: string | null
  tipo_paciente?: PatientType
  especialidad?: string
  stage?: Stage
  health_service_id?: string
  diagnostico?: string
  fecha_ultimos_examenes?: string | null
  es_oncologico?: boolean
  severidad_clinica?: Severity
  estadificacion?: string | null
  telefono_contacto?: string | null
}

/** Alta de un paciente nuevo. */
export interface PatientCreate extends ClinicalStatusUpdate {
  rut: string
  nombre_completo: string
  regimen: Regimen
  especialidad: string
  stage: Stage
  health_service_id: string
  fecha_ingreso_lista?: string | null
  fecha_nacimiento?: string | null
}
