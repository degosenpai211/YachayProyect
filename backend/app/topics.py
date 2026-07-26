"""Temas permitidos del MVP (ciencias escolares Bolivia)."""

TOPICS: dict[str, dict] = {
    "densidad_flotacion": {
        "label": "Densidad y flotación",
        "keywords": ["densidad", "flota", "flotacion", "flotación", "hunde", "huevo", "sal"],
        "allows_experiment": True,
        "example_bo": "En el Salar de Uyuni el agua es tan salada que es más densa y cuesta más hundirse.",
    },
    "fotosintesis": {
        "label": "Fotosíntesis",
        "keywords": ["fotosintesis", "fotosíntesis", "planta", "clorofila", "oxigeno", "oxígeno"],
        "allows_experiment": True,
        "example_bo": "En los yungas paceños las plantas reciben mucha luz y humedad; por eso crecen tan verdes.",
    },
    "estados_materia": {
        "label": "Estados de la materia",
        "keywords": ["solido", "sólido", "liquido", "líquido", "gas", "evapor", "congel", "materia"],
        "allows_experiment": True,
        "example_bo": "El hielo en el altiplano se derrite más lento al sol seco; en el trópico, el agua se evapora rápido.",
    },
    "electricidad_basica": {
        "label": "Electricidad básica",
        "keywords": ["electricidad", "corriente", "circuito", "pila", "voltaje", "resistencia"],
        "allows_experiment": True,
        "example_bo": "Una linterna a pilas en una feria de El Alto funciona igual que un circuito simple de clase.",
    },
    "sistema_digestivo": {
        "label": "Sistema digestivo",
        "keywords": [
            "digestivo",
            "estomago",
            "estómago",
            "intestino",
            "digestión",
            "digestion",
            "salteña",
            "saltena",
            "nutriente",
        ],
        "allows_experiment": True,
        "example_bo": "Cuando comes un salteña, el estómago empieza a triturar y mezclar con jugos digestivos.",
    },
}

TOPIC_IDS = list(TOPICS.keys())


def topic_label(topic_id: str | None) -> str:
    if not topic_id:
        return "Sin tema"
    return TOPICS.get(topic_id, {}).get("label", topic_id)


def classify_topic_heuristic(text: str) -> str | None:
    lowered = text.lower()
    for topic_id, meta in TOPICS.items():
        if any(k in lowered for k in meta["keywords"]):
            return topic_id
    return None


EXPERIMENT_TEMPLATES: dict[str, dict] = {
    "densidad_flotacion": {
        "title": "Huevo que flota con sal",
        "materials": "1 vaso con agua, 1 huevo crudo, 4–6 cucharadas de sal",
        "steps": (
            "1) Pon el huevo en agua pura: se hunde.\n"
            "2) Sácalo y disuelve bastante sal en el vaso.\n"
            "3) Vuelve a poner el huevo: ahora flota.\n"
            "4) Anota qué cambió: la densidad del agua."
        ),
        "explanation": (
            "Al agregar sal, el agua se vuelve más densa. Si la densidad del líquido "
            "supera la del huevo, este flota. Igual idea que en lagos salados de Bolivia."
        ),
    },
    "fotosintesis": {
        "title": "Hoja y luz: ¿dónde hay almidón?",
        "materials": "1 hoja verde, alcohol (con adulto), yodo diluido, luz solar",
        "steps": (
            "1) Deja una hoja al sol unas horas.\n"
            "2) Con ayuda de un adulto, hierve brevemente en alcohol para decolorar.\n"
            "3) Agrega gotas de yodo: zonas oscuras = almidón (producto de la fotosíntesis)."
        ),
        "explanation": "Las plantas usan luz, agua y CO₂ para hacer azúcares/almidón. El yodo lo tiñe de oscuro.",
    },
    "estados_materia": {
        "title": "Agua que cambia de estado",
        "materials": "Vaso con hielo, plato, sol o hornalla (con adulto)",
        "steps": (
            "1) Observa el hielo (sólido).\n"
            "2) Déjalo derretir (líquido).\n"
            "3) Calienta un poco el agua y observa vapor (gas)."
        ),
        "explanation": "Misma sustancia (H₂O), distintos estados según temperatura y energía.",
    },
    "electricidad_basica": {
        "title": "Circuito de linterna",
        "materials": "Pila, cable o clip, foco LED o foco de linterna",
        "steps": (
            "1) Une pila + cable + foco formando un circuito cerrado.\n"
            "2) Si el foco enciende, hay corriente.\n"
            "3) Abre el circuito: se apaga."
        ),
        "explanation": "La corriente necesita un camino cerrado. Interruptor = abrir/cerrar ese camino.",
    },
    "sistema_digestivo": {
        "title": "Modelo de estómago con bolsa",
        "materials": "1 bolsa ziploc, 1 galleta o pan, 2 cucharadas de agua, 1 cucharadita de vinagre (opcional)",
        "steps": (
            "1) Rompe la galleta en trozos (como los dientes Trituran).\n"
            "2) Ponla en la bolsa con un poco de agua (saliva).\n"
            "3) Amasa la bolsa 1 minuto (estómago mezclando).\n"
            "4) Opcional: agrega vinagre (ácido gástrico) y observa cómo se ablanda más.\n"
            "5) Anota: ¿en qué se parece a lo que pasa cuando comes una salteña?"
        ),
        "explanation": (
            "La digestión mecánica (masticar/amasar) y química (jugos ácidos) rompen el alimento "
            "para que el intestino pueda absorber nutrientes."
        ),
    },
}
