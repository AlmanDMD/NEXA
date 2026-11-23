-- =============================================================================
-- PROJETO NEXA — SEED PRELIMINAR DE VALIDAÇÃO N:M: MÓDULO-COMPETÊNCIA (DB-016)
-- SGBD: PostgreSQL 16 (Idempotente — ON CONFLICT DO NOTHING)
-- =============================================================================
-- Valida a relação N:M entre módulos práticos (`learning_modules`) e
-- competências técnicas (`competencies`) com exemplos reais do currículo SENAI
-- (Mecânica Industrial e Metrologia Dimensional), preparando terreno para o
-- seed curricular completo do card `DB-020`.
-- =============================================================================

BEGIN;

-- 1. Curso Técnico SENAI preliminar
INSERT INTO courses (id, code, name, description, total_hours, is_active)
VALUES (
    '10000000-0000-4000-8000-000000000001',
    'TEC-MEC-01',
    'Técnico em Mecânica Industrial',
    'Formação técnica SENAI em usinagem, metrologia dimensional e manutenção mecânica.',
    1200,
    TRUE
)
ON CONFLICT (code) DO NOTHING;

-- 2. Disciplina preliminar (Processos de Fabricação e Metrologia)
INSERT INTO subjects (id, course_id, code, name, workload_hours, syllabus, is_active)
SELECT
    '20000000-0000-4000-8000-000000000001',
    c.id,
    'UC-USIN-01',
    'Processos de Usinagem e Metrologia Aplicada',
    160,
    'Metrologia dimensional com paquímetro/micrômetro e tornearia cilíndrica convencional.',
    TRUE
FROM courses c
WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (course_id, code) DO NOTHING;

-- 3. Módulos práticos sequenciais preliminares
INSERT INTO learning_modules (id, subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT
    '30000000-0000-4000-8000-000000000001',
    s.id,
    'Metrologia com Micrômetro e Paquímetro',
    1,
    'Prática de medição linear e conferência de tolerâncias ISO em bancada.',
    32,
    1.50,
    6.00
FROM subjects s
WHERE s.code = 'UC-USIN-01'
ON CONFLICT (subject_id, order_index) DO NOTHING;

INSERT INTO learning_modules (id, subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT
    '30000000-0000-4000-8000-000000000002',
    s.id,
    'Módulo de Tornearia Cilíndrica',
    2,
    'Faceamento, cilindramento externo e controle dimensional de eixos em torno mecânico.',
    48,
    2.50,
    7.00
FROM subjects s
WHERE s.code = 'UC-USIN-01'
ON CONFLICT (subject_id, order_index) DO NOTHING;

-- 4. Competências técnicas preliminares
INSERT INTO competencies (id, code, title, category, description)
VALUES
    (
        '40000000-0000-4000-8000-000000000001',
        'COMP-MET-01',
        'Medição com Paquímetro e Tolerância H7',
        'TECHNICAL',
        'Executar leitura direta com paquímetro e micrômetro respeitando tolerâncias ISO H7.'
    ),
    (
        '40000000-0000-4000-8000-000000000002',
        'COMP-TOR-01',
        'Operação de Torno Convencional e Cilindramento',
        'TECHNICAL',
        'Selecionar rotação, avanço e ferramenta para usinagem cilíndrica externa.'
    ),
    (
        '40000000-0000-4000-8000-000000000003',
        'COMP-SEG-01',
        'Segurança em Máquinas Operatrizes (NR-12)',
        'SAFETY',
        'Aplicar procedimentos de proteção coletiva, EPIs e parada segura em oficina.'
    ),
    (
        '40000000-0000-4000-8000-000000000004',
        'COMP-PRO-01',
        'Planejamento de Ordem de Serviço de Oficina',
        'PROCEDURAL',
        'Seguir roteiro de fabricação, inspeção intermediária e registro de não conformidades.'
    )
ON CONFLICT (code) DO NOTHING;

-- 5. Vínculos N:M preliminares em `module_competencies` com pesos ponderados e níveis 1..5
INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, c.id, v.weight, v.required_level
FROM (
    VALUES
        (1, 'COMP-MET-01', 2.50::NUMERIC(3,2), 4),
        (1, 'COMP-SEG-01', 1.00::NUMERIC(3,2), 3),
        (1, 'COMP-PRO-01', 1.50::NUMERIC(3,2), 2),
        (2, 'COMP-TOR-01', 3.00::NUMERIC(3,2), 5),
        (2, 'COMP-MET-01', 2.00::NUMERIC(3,2), 4),
        (2, 'COMP-SEG-01', 2.00::NUMERIC(3,2), 5)
) AS v(order_index, comp_code, weight, required_level)
JOIN subjects s ON s.code = 'UC-USIN-01'
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = v.order_index
JOIN competencies c ON c.code = v.comp_code
ON CONFLICT (module_id, competency_id) DO NOTHING;

COMMIT;
