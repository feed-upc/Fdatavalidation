export const COLORS = {
  root:          '#2c3e50',
  group:         '#546e7a',
  dataProduct:   '#e74c3c',
  attribute:     '#f1948a',
  policy:        '#27ae60',
  cdm:           '#e6a817',
  entity:        '#f0c030',
  policyChecker: '#8e44ad',
};

export const LINK_COLORS = {
  hierarchy:     '#bdc3c7',
  hasPolicy:     '#2980b9',
  implementedBy: '#e67e22',
  mapsTo:        '#1abc9c',
  validates:     '#1abc9c',
};

// Expansion links — hidden by default, revealed only in focus mode
export const EXPANSION_LINKS = [
  // PolicyChecker → Attribute (checks)
  { source: 'pc-3ae130f1', target: 'a-pid',           type: 'checks',  label: 'checks' },
  { source: 'pc-5b132606', target: 'a-coa',           type: 'checks',  label: 'checks' },
  { source: 'pc-8524bb89', target: 'a-ph',            type: 'checks',  label: 'checks (null if male)' },
  { source: 'pc-8524bb89', target: 'a-gender',        type: 'uses',    label: 'condition on' },
  { source: 'pc-96133334', target: 'a-gender',        type: 'checks',  label: 'checks distribution' },
  { source: 'pc-32ec32b7', target: 'a-hctry',         type: 'checks',  label: 'checks ISO 3166' },
  { source: 'pc-05fb5861', target: 'a-lu',            type: 'checks',  label: 'checks age ≤ 1440 min' },
  { source: 'pc-69b7c656', target: 'a-ts',            type: 'checks',  label: 'checks age ≤ 30 min' },
  { source: 'pc-21a1ab80', target: 'Patient_Summary', type: 'counts',  label: 'counts rows ≥ 2000' },
  { source: 'pc-32ec32b7', target: 'a-hos-country',  type: 'checks',  label: 'checks ISO 3166 (Hospital)' },

  // Policy Rule → CDM Entity (governs)
  { source: 'DQR1EHRule', target: 'e-PI',  type: 'governs', label: 'governs entity' },
  { source: 'DQR2EHRule', target: 'e-PI',  type: 'governs', label: 'governs entity' },
  { source: 'DQR3EHRule', target: 'e-PSB', type: 'governs', label: 'governs entity' },
  { source: 'DQR5EHRule', target: 'e-PI',  type: 'governs', label: 'governs entity' },
  { source: 'DQR6EHRule', target: 'e-HOS', type: 'governs', label: 'governs entity' },

  // Policy Rule → Attribute (governs specific column)
  { source: 'DQR1EHRule', target: 'a-pid',    type: 'governs', label: 'governs attr.' },
  { source: 'DQR2EHRule', target: 'a-coa',    type: 'governs', label: 'governs attr.' },
  { source: 'DQR3EHRule', target: 'a-ph',     type: 'governs', label: 'governs attr.' },
  { source: 'DQR3EHRule', target: 'a-gender', type: 'governs', label: 'governs attr.' },
  { source: 'DQR5EHRule', target: 'a-gender', type: 'governs', label: 'governs attr.' },
  { source: 'DQR6EHRule', target: 'a-hctry',  type: 'governs', label: 'governs attr.' },
  { source: 'DQR7EHRule', target: 'a-lu',     type: 'governs', label: 'governs attr.' },
  { source: 'DQR1LSRule', target: 'a-ts',     type: 'governs', label: 'governs attr.' },
];

export const EXP_LINK_COLORS = {
  checks:  '#c0392b',
  governs: '#8e44ad',
  uses:    '#d35400',
  counts:  '#27ae60',
};

export const SDM_NODES = [
  // ── Root ──────────────────────────────────────────────────────────────
  { id: 'sdm', type: 'root', label: 'SDM', icon: '⬡',
    detail: { title: 'HealthMesh Semantic Data Model', description: 'Federated data space semantic model for EHDS AMR use case.' } },

  // ── Group hubs ────────────────────────────────────────────────────────
  { id: 'grp-dp',  type: 'group', category: 'dataProduct',   label: 'Data Products',    icon: '⊞' },
  { id: 'grp-pol', type: 'group', category: 'policy',        label: 'ODRL Policies',    icon: '⊛' },
  { id: 'grp-cdm', type: 'group', category: 'cdm',           label: 'Common Data Models', icon: '⊡' },
  { id: 'grp-pc',  type: 'group', category: 'policyChecker', label: 'Policy Checkers',  icon: '⊕' },

  // ── Data Products ─────────────────────────────────────────────────────
  {
    id: 'Patient_Summary', type: 'dataProduct', category: 'dataProduct',
    label: 'Patient Summary',
    detail: {
      title: 'Patient Summary Dataset',
      identifier: '210aa5e4…',
      owner: 'Unknown',
      path: 'DataProduct_EHDS_AMR/Data/Patient_Summary.csv',
      format: 'Tabular (CSV)',
      description: 'EHDS AMR patient data including identification, hospital, and clinical info.',
    },
  },
  {
    id: 'LiveStocks', type: 'dataProduct', category: 'dataProduct',
    label: 'LiveStocks',
    detail: {
      title: 'LiveStocks Dataset',
      path: 'DataProduct_LiveStocks/Data/LiveStocks.csv',
      format: 'Tabular (CSV)',
      description: 'Real-time livestock market data with price and timestamp.',
    },
  },

  {
    id: 'Allergy', type: 'dataProduct', category: 'dataProduct',
    label: 'Allergy',
    detail: {
      title: 'Allergy Dataset',
      path: 'DataProduct_EHDS_AMR/Data/Allergy.csv',
      format: 'Tabular (CSV)',
      description: 'Patient allergy records including agent, severity, and clinical manifestation.',
    },
  },
  {
    id: 'Hospital', type: 'dataProduct', category: 'dataProduct',
    label: 'Hospital',
    detail: {
      title: 'Hospital Dataset',
      path: 'DataProduct_EHDS_AMR/Data/Hospital.csv',
      format: 'Tabular (CSV)',
      description: 'Hospital registry with code, city and ISO country code.',
    },
  },
  {
    id: 'AMR_Study', type: 'dataProduct', category: 'dataProduct',
    label: 'AMR Study',
    detail: {
      title: 'AMR Study Dataset',
      path: 'DataProduct_EHDS_AMR/Data/AMR_Study.csv',
      format: 'Tabular (CSV)',
      description: 'AMR study aggregates: total isolates, specimens, and DQR4EH pass flag.',
    },
  },
  {
    id: 'Isolate', type: 'dataProduct', category: 'dataProduct',
    label: 'Isolate',
    detail: {
      title: 'Isolate Dataset',
      path: 'DataProduct_EHDS_AMR/Data/Isolate.csv',
      format: 'Tabular (CSV)',
      description: 'Individual isolate records: pathogen, antibiotic, resistance result, and small-sample flag.',
    },
  },
  {
    id: 'Pregnancy_History', type: 'dataProduct', category: 'dataProduct',
    label: 'Pregnancy History',
    detail: {
      title: 'Pregnancy History Dataset',
      path: 'DataProduct_EHDS_AMR/Data/Pregnancy_History.csv',
      format: 'Tabular (CSV)',
      description: 'Pregnancy observation records linked to patients.',
    },
  },

  // Attributes — Patient_Summary
  { id: 'a-pid',    type: 'attribute', category: 'dataProduct', label: 'local_patient_id',   parentDP: 'Patient_Summary' },
  { id: 'a-gender', type: 'attribute', category: 'dataProduct', label: 'gender',              parentDP: 'Patient_Summary' },
  { id: 'a-lu',     type: 'attribute', category: 'dataProduct', label: 'lastUpdated',         parentDP: 'Patient_Summary' },
  { id: 'a-hcode',  type: 'attribute', category: 'dataProduct', label: 'hospitalCode',        parentDP: 'Patient_Summary' },
  { id: 'a-hctry',  type: 'attribute', category: 'dataProduct', label: 'hospitalCountry',     parentDP: 'Patient_Summary' },
  { id: 'a-coa',    type: 'attribute', category: 'dataProduct', label: 'countryOfAffiliation',parentDP: 'Patient_Summary' },
  { id: 'a-dob',    type: 'attribute', category: 'dataProduct', label: 'dateOfBirth',         parentDP: 'Patient_Summary' },
  { id: 'a-fn',     type: 'attribute', category: 'dataProduct', label: 'familyName',          parentDP: 'Patient_Summary' },
  { id: 'a-gn',     type: 'attribute', category: 'dataProduct', label: 'givenName',           parentDP: 'Patient_Summary' },
  { id: 'a-ph',     type: 'attribute', category: 'dataProduct', label: 'pregnancyHistory',    parentDP: 'Patient_Summary' },
  // Attributes — LiveStocks
  { id: 'a-price', type: 'attribute', category: 'dataProduct', label: 'price',     parentDP: 'LiveStocks' },
  { id: 'a-ts',    type: 'attribute', category: 'dataProduct', label: 'timestamp', parentDP: 'LiveStocks' },

  // Attributes — Allergy
  { id: 'a-alr-pid',    type: 'attribute', category: 'dataProduct', label: 'patientID',           parentDP: 'Allergy' },
  { id: 'a-alr-desc',   type: 'attribute', category: 'dataProduct', label: 'allergyDescription',  parentDP: 'Allergy' },
  { id: 'a-alr-type',   type: 'attribute', category: 'dataProduct', label: 'typeOfPropensity',    parentDP: 'Allergy' },
  { id: 'a-alr-manif',  type: 'attribute', category: 'dataProduct', label: 'allergyManifestation',parentDP: 'Allergy' },
  { id: 'a-alr-sev',    type: 'attribute', category: 'dataProduct', label: 'severity',            parentDP: 'Allergy' },
  { id: 'a-alr-crit',   type: 'attribute', category: 'dataProduct', label: 'criticality',         parentDP: 'Allergy' },
  { id: 'a-alr-onset',  type: 'attribute', category: 'dataProduct', label: 'onSetDate',           parentDP: 'Allergy' },
  { id: 'a-alr-end',    type: 'attribute', category: 'dataProduct', label: 'endDate',             parentDP: 'Allergy' },
  { id: 'a-alr-status', type: 'attribute', category: 'dataProduct', label: 'status',              parentDP: 'Allergy' },
  { id: 'a-alr-cert',   type: 'attribute', category: 'dataProduct', label: 'certainty',           parentDP: 'Allergy' },
  { id: 'a-alr-agent',  type: 'attribute', category: 'dataProduct', label: 'agentOrAllergen',     parentDP: 'Allergy' },

  // Attributes — Hospital
  { id: 'a-hos-code',    type: 'attribute', category: 'dataProduct', label: 'hospitalCode', parentDP: 'Hospital' },
  { id: 'a-hos-city',    type: 'attribute', category: 'dataProduct', label: 'city',         parentDP: 'Hospital' },
  { id: 'a-hos-country', type: 'attribute', category: 'dataProduct', label: 'country',      parentDP: 'Hospital' },

  // Attributes — AMR_Study
  { id: 'a-amr-sid',    type: 'attribute', category: 'dataProduct', label: 'studyID',        parentDP: 'AMR_Study' },
  { id: 'a-amr-desc',   type: 'attribute', category: 'dataProduct', label: 'description',    parentDP: 'AMR_Study' },
  { id: 'a-amr-tiso',   type: 'attribute', category: 'dataProduct', label: 'totalIsolates',  parentDP: 'AMR_Study' },
  { id: 'a-amr-tspec',  type: 'attribute', category: 'dataProduct', label: 'totalSpecimens', parentDP: 'AMR_Study' },
  { id: 'a-amr-date',   type: 'attribute', category: 'dataProduct', label: 'dateGenerated',  parentDP: 'AMR_Study' },
  { id: 'a-amr-dqr4',   type: 'attribute', category: 'dataProduct', label: 'passesDQR4EH',  parentDP: 'AMR_Study' },

  // Attributes — Isolate
  { id: 'a-iso-id',    type: 'attribute', category: 'dataProduct', label: 'isolateID',            parentDP: 'Isolate' },
  { id: 'a-iso-pid',   type: 'attribute', category: 'dataProduct', label: 'patientID',            parentDP: 'Isolate' },
  { id: 'a-iso-lab',   type: 'attribute', category: 'dataProduct', label: 'laboratoryCode',       parentDP: 'Isolate' },
  { id: 'a-iso-date',  type: 'attribute', category: 'dataProduct', label: 'date',                 parentDP: 'Isolate' },
  { id: 'a-iso-spec',  type: 'attribute', category: 'dataProduct', label: 'specimen',             parentDP: 'Isolate' },
  { id: 'a-iso-path',  type: 'attribute', category: 'dataProduct', label: 'pathogen',             parentDP: 'Isolate' },
  { id: 'a-iso-ab',    type: 'attribute', category: 'dataProduct', label: 'antibiotic',           parentDP: 'Isolate' },
  { id: 'a-iso-res',   type: 'attribute', category: 'dataProduct', label: 'resistanceResult',     parentDP: 'Isolate' },
  { id: 'a-iso-n',     type: 'attribute', category: 'dataProduct', label: 'nIsolates',            parentDP: 'Isolate' },
  { id: 'a-iso-pct',   type: 'attribute', category: 'dataProduct', label: 'resistancePercentage', parentDP: 'Isolate' },
  { id: 'a-iso-flag',  type: 'attribute', category: 'dataProduct', label: 'smallSampleFlag',      parentDP: 'Isolate' },

  // Attributes — Pregnancy_History
  { id: 'a-prh-pid',    type: 'attribute', category: 'dataProduct', label: 'patientID',              parentDP: 'Pregnancy_History' },
  { id: 'a-prh-date',   type: 'attribute', category: 'dataProduct', label: 'dateOfObservation',      parentDP: 'Pregnancy_History' },
  { id: 'a-prh-status', type: 'attribute', category: 'dataProduct', label: 'status',                 parentDP: 'Pregnancy_History' },
  { id: 'a-prh-edd',    type: 'attribute', category: 'dataProduct', label: 'expectedDateOfDelivery', parentDP: 'Pregnancy_History' },

  // ── ODRL Policy Rules ─────────────────────────────────────────────────
  {
    id: 'DQR1EHRule', type: 'policy', category: 'policy', label: 'DQR1EH Rule',
    detail: {
      derivedFrom: 'DQR1EH', dimension: 'Completeness', pattern: 'DQRP2',
      source: 'EHDS Governance Authority',
      statement: 'nationalHealthcarePatientID must not be null (completeness ≥ 100%).',
    },
  },
  {
    id: 'DQR2EHRule', type: 'policy', category: 'policy', label: 'DQR2EH Rule',
    detail: {
      derivedFrom: 'DQR2EH', dimension: 'Compliance', pattern: 'DQRP3',
      source: 'EHDS Governance Authority',
      statement: 'countryOfAffiliation must follow ISO 3166.',
    },
  },
  {
    id: 'DQR3EHRule', type: 'policy', category: 'policy', label: 'DQR3EH Rule',
    detail: {
      derivedFrom: 'DQR3EH', dimension: 'Consistency', pattern: 'DQRP4',
      source: 'EHDS Governance Authority',
      statement: 'pregnancyHistory must be null when gender is male.',
    },
  },
  {
    id: 'DQR4EHRule', type: 'policy', category: 'policy', label: 'DQR4EH Rule',
    detail: {
      derivedFrom: 'DQR4EH', dimension: 'Completeness', pattern: 'DQRP5',
      source: 'EHDS Governance Authority',
      statement: 'Patient Summary must contain at least 2 000 records.',
    },
  },
  {
    id: 'DQR5EHRule', type: 'policy', category: 'policy', label: 'DQR5EH Rule',
    detail: {
      derivedFrom: 'DQR5EH', dimension: 'Fairness', pattern: 'DQRP6',
      source: 'EHDS Governance Authority',
      statement: 'Gender distribution imbalance must not exceed 5% (KL divergence).',
    },
  },
  {
    id: 'DQR6EHRule', type: 'policy', category: 'policy', label: 'DQR6EH Rule',
    detail: {
      derivedFrom: 'DQR6EH', dimension: 'Compliance', pattern: 'DQRP3',
      source: 'EHDS Governance Authority',
      statement: 'Hospital.country must follow ISO 3166.',
    },
  },
  {
    id: 'DQR7EHRule', type: 'policy', category: 'policy', label: 'DQR7EH Rule',
    detail: {
      derivedFrom: 'DQR7EH', dimension: 'Currentness', pattern: 'DQRP1',
      source: 'EHDS Governance Authority',
      statement: 'PatientSummary data age must be ≤ 1 440 minutes (from lastUpdated).',
    },
  },
  {
    id: 'DQR1LSRule', type: 'policy', category: 'policy', label: 'DQR1LS Rule',
    detail: {
      derivedFrom: 'DQR1LS', dimension: 'Timeliness', pattern: 'DQRP1',
      source: 'LiveStocks Authority',
      statement: 'LiveStocks insertionTime age must be ≤ 30 minutes.',
    },
  },

  // ── Common Data Model ─────────────────────────────────────────────────
  {
    id: 'Patient_Data', type: 'cdm', category: 'cdm', label: 'Patient Data CDM',
    detail: {
      owner: 'FederatedTeam', identifier: '123456',
      description: 'EHDS Patient Summary CDM — hierarchical entity structure based on EHDS AMR UML, following FHIR-style entity-scoped element paths.',
    },
  },
  { id: 'e-PS',   type: 'entity', category: 'cdm', label: 'PatientSummary',       parentE: 'Patient_Data' },
  { id: 'e-PSH',  type: 'entity', category: 'cdm', label: 'PatientSummaryHeader', parentE: 'e-PS' },
  { id: 'e-PI',   type: 'entity', category: 'cdm', label: 'PatientIdentification',parentE: 'e-PSH' },
  { id: 'e-AL',   type: 'entity', category: 'cdm', label: 'Alerts',               parentE: 'e-PS' },
  { id: 'e-ALR',  type: 'entity', category: 'cdm', label: 'Allergy',              parentE: 'e-AL' },
  { id: 'e-PSB',  type: 'entity', category: 'cdm', label: 'PatientSummaryBody',   parentE: 'e-PS' },
  { id: 'e-PH',   type: 'entity', category: 'cdm', label: 'PregnancyHistory',        parentE: 'e-PSB' },
  { id: 'e-CPS',  type: 'entity', category: 'cdm', label: 'CurrencyPregnancyStatus', parentE: 'e-PH' },
  { id: 'e-IH',   type: 'entity', category: 'cdm', label: 'IsolateHistory',          parentE: 'e-PSB' },
  { id: 'e-ISO',  type: 'entity', category: 'cdm', label: 'Isolate',                 parentE: 'e-IH' },
  { id: 'e-HOS',  type: 'entity', category: 'cdm', label: 'Hospital',             parentE: 'Patient_Data' },
  { id: 'e-AMR',  type: 'entity', category: 'cdm', label: 'AMRStudy',             parentE: 'Patient_Data' },

  // ── Policy Checkers ───────────────────────────────────────────────────
  {
    id: 'pc-3ae130f1', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR1EH',
    detail: {
      serviceId: 'policyChecker_3ae130f1', dqr: 'DQR1EH',
      expectation: 'ExpectColumnValuesToNotBeNull',
      column: 'local_patient_id', mostly: '100%',
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-5b132606', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR2EH',
    detail: {
      serviceId: 'policyChecker_5b132606', dqr: 'DQR2EH',
      expectation: 'ExpectColumnValuesToBeInSet',
      column: 'countryOfAffiliation', valueSet: 'ISO 3166-1 alpha-2',
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-8524bb89', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR3EH',
    detail: {
      serviceId: 'policyChecker_8524bb89', dqr: 'DQR3EH',
      expectation: 'ExpectColumnValuesToBeNull (conditional)',
      column: 'pregnancyHistory', condition: 'gender == "male"',
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-21a1ab80', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR4EH',
    detail: {
      serviceId: 'policyChecker_21a1ab80', dqr: 'DQR4EH',
      expectation: 'ExpectTableRowCountToBeBetween',
      minValue: 2000, maxValue: '∞',
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-96133334', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR5EH',
    detail: {
      serviceId: 'policyChecker_96133334', dqr: 'DQR5EH',
      expectation: 'ExpectColumnKLDivergenceToBeLessThan',
      column: 'gender', threshold: 0.05, distribution: '[M:0.5, F:0.5]',
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-32ec32b7', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR6EH',
    detail: {
      serviceId: 'policyChecker_32ec32b7', dqr: 'DQR6EH',
      expectation: 'ExpectColumnValuesToBeInSet',
      column: 'country', valueSet: 'ISO 3166-1 alpha-2',
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-05fb5861', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR7EH',
    detail: {
      serviceId: 'policyChecker_05fb5861', dqr: 'DQR7EH',
      expectation: 'ExpectColumnValuesToBeBetween',
      column: 'lastUpdated_age_minutes', min: 0, max: 1440,
      dataProduct: 'Patient_Summary',
    },
  },
  {
    id: 'pc-69b7c656', type: 'policyChecker', category: 'policyChecker', label: 'PC · DQR1LS',
    detail: {
      serviceId: 'policyChecker_69b7c656', dqr: 'DQR1LS',
      expectation: 'ExpectColumnValuesToBeBetween',
      column: 'insertionTime_age_minutes', min: 0, max: 30,
      dataProduct: 'LiveStocks',
    },
  },
];

export const SDM_LINKS = [
  // Root → group hubs
  { source: 'sdm', target: 'grp-dp',  type: 'hierarchy' },
  { source: 'sdm', target: 'grp-pol', type: 'hierarchy' },
  { source: 'sdm', target: 'grp-cdm', type: 'hierarchy' },
  { source: 'sdm', target: 'grp-pc',  type: 'hierarchy' },

  // Groups → data products
  { source: 'grp-dp', target: 'Patient_Summary',    type: 'hierarchy' },
  { source: 'grp-dp', target: 'LiveStocks',          type: 'hierarchy' },
  { source: 'grp-dp', target: 'Allergy',             type: 'hierarchy' },
  { source: 'grp-dp', target: 'Hospital',            type: 'hierarchy' },
  { source: 'grp-dp', target: 'AMR_Study',           type: 'hierarchy' },
  { source: 'grp-dp', target: 'Isolate',             type: 'hierarchy' },
  { source: 'grp-dp', target: 'Pregnancy_History',   type: 'hierarchy' },

  // Data products → attributes
  { source: 'Patient_Summary', target: 'a-pid',    type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-gender', type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-lu',     type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-hcode',  type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-hctry',  type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-coa',    type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-dob',    type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-fn',     type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-gn',     type: 'hierarchy' },
  { source: 'Patient_Summary', target: 'a-ph',     type: 'hierarchy' },
  { source: 'LiveStocks', target: 'a-price', type: 'hierarchy' },
  { source: 'LiveStocks', target: 'a-ts',    type: 'hierarchy' },

  // Allergy → attributes
  { source: 'Allergy', target: 'a-alr-pid',    type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-desc',   type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-type',   type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-manif',  type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-sev',    type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-crit',   type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-onset',  type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-end',    type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-status', type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-cert',   type: 'hierarchy' },
  { source: 'Allergy', target: 'a-alr-agent',  type: 'hierarchy' },

  // Hospital → attributes
  { source: 'Hospital', target: 'a-hos-code',    type: 'hierarchy' },
  { source: 'Hospital', target: 'a-hos-city',    type: 'hierarchy' },
  { source: 'Hospital', target: 'a-hos-country', type: 'hierarchy' },

  // AMR_Study → attributes
  { source: 'AMR_Study', target: 'a-amr-sid',   type: 'hierarchy' },
  { source: 'AMR_Study', target: 'a-amr-desc',  type: 'hierarchy' },
  { source: 'AMR_Study', target: 'a-amr-tiso',  type: 'hierarchy' },
  { source: 'AMR_Study', target: 'a-amr-tspec', type: 'hierarchy' },
  { source: 'AMR_Study', target: 'a-amr-date',  type: 'hierarchy' },
  { source: 'AMR_Study', target: 'a-amr-dqr4',  type: 'hierarchy' },

  // Isolate → attributes
  { source: 'Isolate', target: 'a-iso-id',   type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-pid',  type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-lab',  type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-date', type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-spec', type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-path', type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-ab',   type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-res',  type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-n',    type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-pct',  type: 'hierarchy' },
  { source: 'Isolate', target: 'a-iso-flag', type: 'hierarchy' },

  // Pregnancy_History → attributes
  { source: 'Pregnancy_History', target: 'a-prh-pid',    type: 'hierarchy' },
  { source: 'Pregnancy_History', target: 'a-prh-date',   type: 'hierarchy' },
  { source: 'Pregnancy_History', target: 'a-prh-status', type: 'hierarchy' },
  { source: 'Pregnancy_History', target: 'a-prh-edd',    type: 'hierarchy' },

  // Groups → policy rules
  { source: 'grp-pol', target: 'DQR1EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR2EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR3EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR4EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR5EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR6EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR7EHRule', type: 'hierarchy' },
  { source: 'grp-pol', target: 'DQR1LSRule', type: 'hierarchy' },

  // Groups → CDM
  { source: 'grp-cdm', target: 'Patient_Data', type: 'hierarchy' },
  { source: 'Patient_Data', target: 'e-PS',  type: 'hierarchy' },
  { source: 'e-PS',  target: 'e-PSH', type: 'hierarchy' },
  { source: 'e-PSH', target: 'e-PI',  type: 'hierarchy' },
  { source: 'e-PS',  target: 'e-AL',  type: 'hierarchy' },
  { source: 'e-AL',  target: 'e-ALR', type: 'hierarchy' },
  { source: 'e-PS',  target: 'e-PSB', type: 'hierarchy' },
  { source: 'e-PSB', target: 'e-PH',  type: 'hierarchy' },
  { source: 'e-PH',  target: 'e-CPS', type: 'hierarchy' },
  { source: 'e-PSB', target: 'e-IH',  type: 'hierarchy' },
  { source: 'e-IH',  target: 'e-ISO', type: 'hierarchy' },
  { source: 'Patient_Data', target: 'e-HOS', type: 'hierarchy' },
  { source: 'Patient_Data', target: 'e-AMR', type: 'hierarchy' },

  // Groups → policy checkers
  { source: 'grp-pc', target: 'pc-3ae130f1', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-5b132606', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-8524bb89', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-21a1ab80', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-96133334', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-32ec32b7', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-05fb5861', type: 'hierarchy' },
  { source: 'grp-pc', target: 'pc-69b7c656', type: 'hierarchy' },

  // ── Cross-domain: hasPolicy ───────────────────────────────────────────
  { source: 'Patient_Summary', target: 'DQR1EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Patient_Summary', target: 'DQR2EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Patient_Summary', target: 'DQR3EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Patient_Summary', target: 'DQR4EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Patient_Summary', target: 'DQR5EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Patient_Summary', target: 'DQR6EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Patient_Summary', target: 'DQR7EHRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'LiveStocks',      target: 'DQR1LSRule', type: 'hasPolicy', label: 'hasPolicy' },
  { source: 'Hospital',        target: 'DQR6EHRule', type: 'hasPolicy', label: 'hasPolicy' },

  // ── Cross-domain: implementedBy ───────────────────────────────────────
  { source: 'DQR1EHRule', target: 'pc-3ae130f1', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR2EHRule', target: 'pc-5b132606', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR3EHRule', target: 'pc-8524bb89', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR4EHRule', target: 'pc-21a1ab80', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR5EHRule', target: 'pc-96133334', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR6EHRule', target: 'pc-32ec32b7', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR7EHRule', target: 'pc-05fb5861', type: 'implementedBy', label: 'implementedBy' },
  { source: 'DQR1LSRule', target: 'pc-69b7c656', type: 'implementedBy', label: 'implementedBy' },

  // ── Cross-domain: mapsTo (CDM ↔ DataProduct) ─────────────────────────
  { source: 'Patient_Data',     target: 'Patient_Summary',  type: 'mapsTo', label: 'mapsTo' },
  { source: 'e-ALR',            target: 'Allergy',           type: 'mapsTo', label: 'mapsTo' },
  { source: 'e-HOS',            target: 'Hospital',          type: 'mapsTo', label: 'mapsTo' },
  { source: 'e-AMR',            target: 'AMR_Study',         type: 'mapsTo', label: 'mapsTo' },
  { source: 'e-ISO',            target: 'Isolate',           type: 'mapsTo', label: 'mapsTo' },
  { source: 'e-CPS',            target: 'Pregnancy_History', type: 'mapsTo', label: 'mapsTo' },
];
