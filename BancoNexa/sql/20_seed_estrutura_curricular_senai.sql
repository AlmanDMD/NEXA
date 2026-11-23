-- =============================================================================
-- PROJETO NEXA — SEED IDEMPOTENTE DE ESTRUTURA CURRICULAR SENAI (DB-020)
-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)
-- Dados 100% anônimos e fictícios para ambiente de desenvolvimento/testes
-- =============================================================================

BEGIN;

-- 1. Curso Técnico SENAI (1 curso)
INSERT INTO courses (code, name, description, total_hours, is_active)
VALUES ('TEC-MEC-01', 'Curso Técnico em Mecânica Industrial', 'Formação técnica profissionalizante SENAI voltada para metrologia dimensional, desenho técnico mecânico, processos de usinagem convencional e segurança industrial.', 1200, TRUE)
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name, description = EXCLUDED.description, total_hours = EXCLUDED.total_hours, is_active = EXCLUDED.is_active;

-- 2. Turmas Acadêmicas SENAI (2 turmas: MEC-2026-1 e MEC-2026-2)
INSERT INTO classes (course_id, code, period, shift, max_students, status, start_date, end_date)
SELECT c.id, 'MEC-2026-1', '2026.1', 'MORNING'::shift_enum, 30, 'ACTIVE'::class_status_enum, DATE '2026-02-09', DATE '2026-07-10'
FROM courses c WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (code, period) DO UPDATE
SET shift = EXCLUDED.shift, max_students = EXCLUDED.max_students, status = EXCLUDED.status, start_date = EXCLUDED.start_date, end_date = EXCLUDED.end_date;

INSERT INTO classes (course_id, code, period, shift, max_students, status, start_date, end_date)
SELECT c.id, 'MEC-2026-2', '2026.2', 'NIGHT'::shift_enum, 30, 'ACTIVE'::class_status_enum, DATE '2026-08-03', DATE '2026-12-18'
FROM courses c WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (code, period) DO UPDATE
SET shift = EXCLUDED.shift, max_students = EXCLUDED.max_students, status = EXCLUDED.status, start_date = EXCLUDED.start_date, end_date = EXCLUDED.end_date;

-- 3. Disciplinas Teórico-Práticas SENAI (4 disciplinas)
INSERT INTO subjects (course_id, code, name, workload_hours, syllabus, is_active)
SELECT c.id, 'UC-MET-01', 'Metrologia', 80, 'Sistemas de unidades, medição linear com paquímetro e micrômetro, relógio comparador, incerteza de medição e controle dimensional ISO.', TRUE
FROM courses c WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (course_id, code) DO UPDATE
SET name = EXCLUDED.name, workload_hours = EXCLUDED.workload_hours, syllabus = EXCLUDED.syllabus, is_active = EXCLUDED.is_active;

INSERT INTO subjects (course_id, code, name, workload_hours, syllabus, is_active)
SELECT c.id, 'UC-DTM-02', 'Desenho Técnico Mecânico', 80, 'Projeções ortográficas ABNT, cortes e seções, cotagem funcional, tolerâncias dimensionais, ajustes eixo-furo e simbologia de rugosidade.', TRUE
FROM courses c WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (course_id, code) DO UPDATE
SET name = EXCLUDED.name, workload_hours = EXCLUDED.workload_hours, syllabus = EXCLUDED.syllabus, is_active = EXCLUDED.is_active;

INSERT INTO subjects (course_id, code, name, workload_hours, syllabus, is_active)
SELECT c.id, 'UC-USI-03', 'Usinagem Convencional', 160, 'Parâmetros de corte, torneamento cilíndrico e faceamento em torno convencional, fresamento de superfícies planas, rasgos e acabamento.', TRUE
FROM courses c WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (course_id, code) DO UPDATE
SET name = EXCLUDED.name, workload_hours = EXCLUDED.workload_hours, syllabus = EXCLUDED.syllabus, is_active = EXCLUDED.is_active;

INSERT INTO subjects (course_id, code, name, workload_hours, syllabus, is_active)
SELECT c.id, 'UC-SEG-04', 'Segurança do Trabalho', 40, 'Prevenção de acidentes em oficinas mecânicas, uso de EPIs/EPCs, requisitos de segurança em máquinas operatrizes (NR-12) e programa 5S.', TRUE
FROM courses c WHERE c.code = 'TEC-MEC-01'
ON CONFLICT (course_id, code) DO UPDATE
SET name = EXCLUDED.name, workload_hours = EXCLUDED.workload_hours, syllabus = EXCLUDED.syllabus, is_active = EXCLUDED.is_active;

-- 4. Módulos de Aprendizagem Prática SENAI (8 módulos sequenciais)
INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Metrologia com Paquímetro e Régua Graduada', 1, 'Leitura direta em milímetros e polegadas com paquímetro universal, conferência de peças padronizadas e verificação de tolerância H7.', 24, 1.00, 6.00
FROM subjects s WHERE s.code = 'UC-MET-01'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Metrologia com Micrômetro e Relógio Comparador', 2, 'Medição centesimal externa com micrômetro, verificação de concentricidade e batimento radial em peças cilíndricas usinadas.', 32, 1.50, 6.50
FROM subjects s WHERE s.code = 'UC-MET-01'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Leitura de Vistas Ortográficas, Cortes e Cotagem', 1, 'Interpretação prática de desenhos industriais em 1º diedro, cortes parciais/totais e extração de cotas críticas para fabricação.', 20, 1.00, 6.00
FROM subjects s WHERE s.code = 'UC-DTM-02'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Tolerâncias Dimensionais ISO, Ajustes e Rugosidade', 2, 'Análise de campos de tolerância ISO 286, seleção de ajustes com folga/interferência e leitura de especificações de rugosidade Ra e GD&T.', 28, 1.50, 6.50
FROM subjects s WHERE s.code = 'UC-DTM-02'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Módulo de Tornearia Cilíndrica e Faceamento', 1, 'Preparação de torno paralelo, centralização de ferramenta, cálculo de RPM, faceamento e cilindramento externo de eixos escalonados.', 56, 2.00, 7.00
FROM subjects s WHERE s.code = 'UC-USI-03'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Módulo de Fresamento de Superfícies Planas e Rasgos', 2, 'Fixação em morsa de precisão, alinhamento de cabeçote, esquadrejamento de blocos prismáticos e abertura de canais chavetados.', 56, 2.00, 7.00
FROM subjects s WHERE s.code = 'UC-USI-03'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Segurança em Oficinas Mecânicas e Uso de EPIs', 1, 'Inspeção pré-operacional de bancada, identificação de riscos mecânicos/térmicos e utilização obrigatória de EPIs de proteção.', 16, 1.00, 7.00
FROM subjects s WHERE s.code = 'UC-SEG-04'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

INSERT INTO learning_modules (subject_id, title, order_index, description, practical_hours, module_weight, passing_score)
SELECT s.id, 'Bloqueio de Máquinas Operatrizes (NR-12) e 5S', 2, 'Procedimentos de bloqueio e etiquetagem (LOTO), teste de botoeiras de emergência NR-12, segregação de cavacos e organização 5S.', 16, 1.50, 7.50
FROM subjects s WHERE s.code = 'UC-SEG-04'
ON CONFLICT (subject_id, order_index) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, practical_hours = EXCLUDED.practical_hours, module_weight = EXCLUDED.module_weight, passing_score = EXCLUDED.passing_score;

-- 5. Competências e Habilidades Técnicas Industriais (15 competências)
INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-MET-01', 'Medição com Paquímetro e Tolerância H7', 'TECHNICAL'::competency_category_enum, 'Realizar medições externas, internas e de profundidade com resolução de 0,02 mm segundo ISO 286.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-MET-02', 'Medição de Precisão com Micrômetro Externo', 'TECHNICAL'::competency_category_enum, 'Operar micrômetro externo centesimal com controle de força de catraca e leitura sem erro de paralaxe.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-MET-03', 'Verificação de Batimento com Relógio Comparador', 'TECHNICAL'::competency_category_enum, 'Posicionar base magnética e relógio comparador para inspecionar desvios geométricos e concentricidade.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-MET-04', 'Conservação e Calibração de Instrumentos de Medição', 'PROCEDURAL'::competency_category_enum, 'Conferir zeragem com padrões de referência, higienizar e acondicionar instrumentos metrológicos.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-DTM-01', 'Interpretação de Vistas Ortográficas e Cortes ABNT', 'TECHNICAL'::competency_category_enum, 'Ler projeções em 1º diedro, hachuras de corte e linhas de centro conforme NBR 10067.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-DTM-02', 'Leitura de Tolerâncias ISO e Ajustes Eixo-Furo', 'TECHNICAL'::competency_category_enum, 'Determinar afastamentos superior/inferior e classificar ajustes com folga, incerto ou interferência.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-DTM-03', 'Análise de Rugosidade Superficial e Simbologia GD&T', 'PROCEDURAL'::competency_category_enum, 'Interpretar símbolos de rugosidade Ra e tolerâncias geométricas de forma e posição no desenho.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-USI-01', 'Faceamento e Cilindramento Externo em Torno Convencional', 'TECHNICAL'::competency_category_enum, 'Usinar eixos cilíndricos em torno paralelo mantendo coaxialidade, acabamento e cota dentro do desenho.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-USI-02', 'Cálculo de RPM, Avanço e Profundidade de Corte', 'TECHNICAL'::competency_category_enum, 'Calcular velocidade de corte e rotação adequada conforme material da peça e geometria da ferramenta.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-USI-03', 'Fresamento de Superfícies Planas e Canais Chavetados', 'TECHNICAL'::competency_category_enum, 'Executar esquadrejamento de blocos e usinagem de rasgos precisos em fresadora ferramenteira.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-USI-04', 'Fixação de Peças, Alinhamento de Placa e Ordem de Serviço', 'PROCEDURAL'::competency_category_enum, 'Planejar sequência de usinagem, fixar peça com segurança na placa/morsa e registrar inspeções na OS.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-SEG-01', 'Seleção e Uso Correto de EPIs em Oficina Mecânica', 'SAFETY'::competency_category_enum, 'Utilizar óculos de proteção, calçado de segurança e vestimenta ajustada sem adornos em máquinas rotativas.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-SEG-02', 'Operação Segura de Máquinas Operatrizes conforme NR-12', 'SAFETY'::competency_category_enum, 'Verificar proteções móveis, intertravamentos e áreas de risco antes de acionar torno ou fresadora.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-SEG-03', 'Bloqueio, Sinalização e Parada de Emergência em Bancada', 'SAFETY'::competency_category_enum, 'Executar procedimentos de desenergização segura e acionamento correto de dispositivos de emergência.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

INSERT INTO competencies (code, title, category, description)
VALUES ('COMP-PRO-01', 'Organização de Bancada, Descarte de Cavacos e Metodologia 5S', 'PROCEDURAL'::competency_category_enum, 'Manter ferramentas organizadas, remover cavacos com escova adequada e zelar pela limpeza da oficina.')
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description;

-- 6. Relacionamento N:M Módulo-Competência (24 vínculos ponderados)
INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.50, 3
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-04'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.00, 2
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-PRO-01'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-MET-02'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.00, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-MET-03'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-MET-04'
WHERE s.code = 'UC-MET-01'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-DTM-01'
WHERE s.code = 'UC-DTM-02'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.00, 3
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-01'
WHERE s.code = 'UC-DTM-02'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-DTM-02'
WHERE s.code = 'UC-DTM-02'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.00, 3
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-DTM-03'
WHERE s.code = 'UC-DTM-02'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.00, 3
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-MET-02'
WHERE s.code = 'UC-DTM-02'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 3.00, 5
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-01'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.00, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-02'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-USI-04'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-MET-02'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.00, 5
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 3.00, 5
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-USI-03'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.00, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-USI-02'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-USI-04'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.00, 5
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
WHERE s.code = 'UC-USI-03'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 4
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-SEG-01'
WHERE s.code = 'UC-SEG-04'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 1.50, 3
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 1
JOIN competencies cp ON cp.code = 'COMP-PRO-01'
WHERE s.code = 'UC-SEG-04'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 5
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-SEG-02'
WHERE s.code = 'UC-SEG-04'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

INSERT INTO module_competencies (module_id, competency_id, weight, required_level)
SELECT m.id, cp.id, 2.50, 5
FROM subjects s
JOIN learning_modules m ON m.subject_id = s.id AND m.order_index = 2
JOIN competencies cp ON cp.code = 'COMP-SEG-03'
WHERE s.code = 'UC-SEG-04'
ON CONFLICT (module_id, competency_id) DO UPDATE
SET weight = EXCLUDED.weight, required_level = EXCLUDED.required_level;

-- 7. Usuários Fictícios Anônimos e Perfis (zero dados pessoais reais)
INSERT INTO users (email, password_hash, role, is_active)
VALUES ('coord.demo@senai.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'COORDINATOR'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Coordenacao Demo SENAI', 'SENAI-COORD-0001', 'Conta fictícia de demonstração da coordenação pedagógica.'
FROM users u WHERE u.email = 'coord.demo@senai.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('instrutor.teoria.demo@senai.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'TEACHER'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Instrutor Demo 01 (Metrologia e Desenho)', 'SENAI-DOC-0001', 'Instrutor fictício de metrologia dimensional, desenho técnico e teoria de usinagem.'
FROM users u WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('instrutor.oficina.demo@senai.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'TEACHER'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Instrutor Demo 02 (Oficina de Usinagem e NR-12)', 'SENAI-DOC-0002', 'Instrutor fictício de laboratório de tornearia, fresamento e segurança industrial.'
FROM users u WHERE u.email = 'instrutor.oficina.demo@senai.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo01@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 01', 'SENAI-2026-0001', 'Estudante fictício da turma MEC-2026-1.'
FROM users u WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo02@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 02', 'SENAI-2026-0002', 'Estudante fictício da turma MEC-2026-1.'
FROM users u WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo03@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 03', 'SENAI-2026-0003', 'Estudante fictício da turma MEC-2026-1.'
FROM users u WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo04@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 04', 'SENAI-2026-0004', 'Estudante fictício da turma MEC-2026-2.'
FROM users u WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo05@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 05', 'SENAI-2026-0005', 'Estudante fictício da turma MEC-2026-2.'
FROM users u WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

INSERT INTO users (email, password_hash, role, is_active)
VALUES ('estudante.demo06@aluno.nexa.local', '$2b$12$NexaSenaiDemoSeed20260uQwErTyUiOpAsDfGhJkLzXcVbNm1234', 'STUDENT'::user_role_enum, TRUE)
ON CONFLICT (email) DO UPDATE
SET role = EXCLUDED.role, is_active = EXCLUDED.is_active;
INSERT INTO user_profiles (user_id, full_name, registration_number, bio)
SELECT u.id, 'Estudante Demo 06', 'SENAI-2026-0006', 'Estudante fictício da turma MEC-2026-2.'
FROM users u WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (user_id) DO UPDATE
SET full_name = EXCLUDED.full_name, registration_number = EXCLUDED.registration_number, bio = EXCLUDED.bio;

-- 8. Matrículas Fictícias de Estudantes nas Turmas MEC-2026-1 e MEC-2026-2
INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, NULL, 96.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-02', 'ACTIVE'::enrollment_status_enum, NULL, 88.50
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-02-03', 'ACTIVE'::enrollment_status_enum, NULL, 72.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, NULL, 94.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-27', 'ACTIVE'::enrollment_status_enum, NULL, 85.00
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo05@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

INSERT INTO enrollments (student_id, class_id, enrollment_date, status, final_grade, attendance_rate)
SELECT u.id, cl.id, DATE '2026-07-28', 'ACTIVE'::enrollment_status_enum, NULL, 78.50
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
WHERE u.email = 'estudante.demo06@aluno.nexa.local'
ON CONFLICT (student_id, class_id) DO UPDATE
SET status = EXCLUDED.status, final_grade = EXCLUDED.final_grade, attendance_rate = EXCLUDED.attendance_rate;

-- 9. Alocação de Docentes nas Turmas e Disciplinas (RBAC Contextual)
INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-MET-01'
WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-DTM-02'
WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-USI-03'
WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, FALSE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-USI-03'
WHERE u.email = 'instrutor.oficina.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN subjects s ON s.code = 'UC-SEG-04'
WHERE u.email = 'instrutor.oficina.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-MET-01'
WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-DTM-02'
WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-USI-03'
WHERE u.email = 'instrutor.oficina.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, FALSE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-USI-03'
WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

INSERT INTO teacher_assignments (teacher_id, class_id, subject_id, is_main_teacher)
SELECT u.id, cl.id, s.id, TRUE
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN subjects s ON s.code = 'UC-SEG-04'
WHERE u.email = 'instrutor.oficina.demo@senai.nexa.local'
ON CONFLICT (teacher_id, class_id, subject_id) DO UPDATE
SET is_main_teacher = EXCLUDED.is_main_teacher;

COMMIT;
