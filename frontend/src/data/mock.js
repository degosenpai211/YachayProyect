/** Fallback si el backend aún no responde */
export const MOCK_STATS = {
  students: 4,
  messages: 7,
  active_weaknesses: 2,
  experiments: 1,
  topics: [
    {
      topic: "densidad_flotacion",
      topic_label: "Densidad y flotación",
      student_count: 1,
      total_hits: 2,
    },
    {
      topic: "electricidad_basica",
      topic_label: "Electricidad básica",
      student_count: 1,
      total_hits: 2,
    },
  ],
};

export const MOCK_STUDENTS = [
  {
    id: 1,
    code: "UEBOL-3A-01",
    display_name: "Ana Quispe",
    course: "UEBOL-3A",
    weakness_count: 1,
    message_count: 3,
  },
  {
    id: 2,
    code: "UEBOL-3A-07",
    display_name: "Luis Mamani",
    course: "UEBOL-3A",
    weakness_count: 0,
    message_count: 2,
  },
  {
    id: 3,
    code: "UEBOL-3A-12",
    display_name: "María Condori",
    course: "UEBOL-3A",
    weakness_count: 1,
    message_count: 2,
  },
  {
    id: 4,
    code: "UEBOL-3B-03",
    display_name: "Diego Flores",
    course: "UEBOL-3B",
    weakness_count: 0,
    message_count: 0,
  },
];

export const MOCK_WEAKNESSES = [
  {
    id: 1,
    student_code: "UEBOL-3A-01",
    student_name: "Ana Quispe",
    topic: "densidad_flotacion",
    hit_count: 2,
  },
  {
    id: 2,
    student_code: "UEBOL-3A-12",
    student_name: "María Condori",
    topic: "electricidad_basica",
    hit_count: 2,
  },
];

export const MOCK_EXPERIMENTS = [
  {
    id: 1,
    student_code: "UEBOL-3A-01",
    student_name: "Ana Quispe",
    topic: "densidad_flotacion",
    title: "Huevo que flota con sal",
    materials: "Vaso, agua, huevo, sal",
    steps: "1) Huevo en agua. 2) Agregar sal. 3) Observar flotación.",
    explanation: "El agua salada es más densa y sostiene al huevo.",
  },
];

export const TOPIC_LABELS = {
  densidad_flotacion: "Densidad y flotación",
  fotosintesis: "Fotosíntesis",
  estados_materia: "Estados de la materia",
  electricidad_basica: "Electricidad básica",
  sistema_digestivo: "Sistema digestivo",
};
