-- =============================================================================
-- PROJETO NEXA — SEED IDEMPOTENTE DO LOTE 5: COMUNICAÇÃO & GAMIFICAÇÃO (DB-045)
-- SGBD: PostgreSQL 16 (UPSERT via ON CONFLICT DO UPDATE)
-- Popula conquistas técnicas SENAI (gamification_badges), conquistas de alunos,
-- avisos de mural, solicitações confidenciais, notas pedagógicas e mensagens.
-- =============================================================================

BEGIN;

-- 1. Mural de Avisos da Turma (class_announcements — DB-041)
INSERT INTO class_announcements (id, class_id, subject_id, author_id, title, content, priority, is_pinned, published_at, expires_at)
SELECT '51000000-0000-4000-8000-000000000001'::uuid, cl.id, s.id, u.id, 'Uso Obrigatório de Óculos de Proteção e Calçado NR-12 na Oficina de Tornearia', 'Lembramos a todos os estudantes que a entrada na Oficina de Tornearia 02 exige óculos de proteção incolor, avental e calçado de segurança com biqueira.', 'URGENT'::announcement_priority_enum, TRUE, TIMESTAMPTZ '2026-03-09T11:00:00Z', TIMESTAMPTZ '2026-07-10T23:59:00Z'
FROM classes cl
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN users u ON u.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, content = EXCLUDED.content, priority = EXCLUDED.priority, is_pinned = EXCLUDED.is_pinned;

INSERT INTO class_announcements (id, class_id, subject_id, author_id, title, content, priority, is_pinned, published_at, expires_at)
SELECT '51000000-0000-4000-8000-000000000002'::uuid, cl.id, s.id, u.id, 'Horário Extra de Monitoria em Micrômetro Externo e Relógio Comparador', 'O Laboratório de Metrologia 01 estará aberto às quintas-feiras das 13h30 às 15h30 para reforço prático de leitura centesimal.', 'IMPORTANT'::announcement_priority_enum, FALSE, TIMESTAMPTZ '2026-03-14T14:00:00Z', NULL
FROM classes cl
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN users u ON u.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, content = EXCLUDED.content, priority = EXCLUDED.priority, is_pinned = EXCLUDED.is_pinned;

INSERT INTO class_announcements (id, class_id, subject_id, author_id, title, content, priority, is_pinned, published_at, expires_at)
SELECT '51000000-0000-4000-8000-000000000003'::uuid, cl.id, NULL, u.id, 'Calendário de Avaliações Práticas e Fechamento do 1º Bimestre', 'A coordenação pedagógica divulgou o cronograma oficial das bancas práticas de Usinagem e Metrologia para a turma MEC-2026-2.', 'NORMAL'::announcement_priority_enum, TRUE, TIMESTAMPTZ '2026-08-18T12:00:00Z', NULL
FROM classes cl
JOIN users u ON u.email = 'coordenacao.demo@senai.nexa.local'
WHERE cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title, content = EXCLUDED.content, priority = EXCLUDED.priority, is_pinned = EXCLUDED.is_pinned;

-- 2. Solicitações Confidenciais de Apoio (help_requests — DB-042)
INSERT INTO help_requests (id, student_id, enrollment_id, subject_id, module_id, assigned_teacher_id, category, subject_title, description, is_confidential, status, resolution_summary, closed_at)
SELECT '52000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, s.id, lm.id, t.id, 'PRACTICAL_DIFFICULTY'::help_request_category_enum, 'Dificuldade na centragem da ferramenta de corte no torno paralelo', 'Estou errando a altura da ponta da ferramenta no faceamento e gerando ressalto no centro da peça. Gostaria de agendar apoio reservado na bancada.', TRUE, 'IN_PROGRESS'::help_request_status_enum, NULL, NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN subjects s ON s.code = 'UC-USI-03'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 1
JOIN users t ON t.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET status = EXCLUDED.status, resolution_summary = EXCLUDED.resolution_summary, closed_at = EXCLUDED.closed_at;

INSERT INTO help_requests (id, student_id, enrollment_id, subject_id, module_id, assigned_teacher_id, category, subject_title, description, is_confidential, status, resolution_summary, closed_at)
SELECT '52000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, s.id, lm.id, t.id, 'TECHNICAL_DOUBT'::help_request_category_enum, 'Dúvida na leitura de meio milímetro no tambor do micrômetro', 'Confundo quando somar 0,50mm na bainha do micrômetro externo durante a inspeção de eixos H7.', TRUE, 'RESOLVED'::help_request_status_enum, 'Realizada demonstração individual de 20 minutos com calibrador padrão de 25mm e lista de 10 leituras validadas.', NULL
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN subjects s ON s.code = 'UC-MET-01'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users t ON t.email = 'instrutor.teoria.demo@senai.nexa.local'
WHERE u.email = 'estudante.demo14@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET status = EXCLUDED.status, resolution_summary = EXCLUDED.resolution_summary, closed_at = EXCLUDED.closed_at;

INSERT INTO help_requests (id, student_id, enrollment_id, subject_id, module_id, assigned_teacher_id, category, subject_title, description, is_confidential, status, resolution_summary, closed_at)
SELECT '52000000-0000-4000-8000-000000000003'::uuid, u.id, e.id, s.id, lm.id, t.id, 'PERSONAL_PEDAGOGICAL'::help_request_category_enum, 'Reposição de aula prática por mudança de escala no trabalho', 'Tive alteração temporária de turno na empresa e preciso alinhar reposição para não ultrapassar o limite de 25% de faltas.', TRUE, 'CLOSED'::help_request_status_enum, 'Plano de reposição homologado pela coordenação com assinatura de termo e reagendamento para sábado letivo.', TIMESTAMPTZ '2026-09-12T17:30:00Z'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN subjects s ON s.code = 'UC-SEG-04'
JOIN learning_modules lm ON lm.subject_id = s.id AND lm.order_index = 2
JOIN users t ON t.email = 'coordenacao.demo@senai.nexa.local'
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET status = EXCLUDED.status, resolution_summary = EXCLUDED.resolution_summary, closed_at = EXCLUDED.closed_at;

-- 3. Observações Pedagógicas Restritas (pedagogical_notes — DB-043)
INSERT INTO pedagogical_notes (id, student_id, enrollment_id, author_id, visibility_scope, category, note_content, requires_followup, followup_date)
SELECT '53000000-0000-4000-8000-000000000001'::uuid, u.id, e.id, a.id, 'TEACHERS_AND_COORD'::note_visibility_scope_enum, 'INTERVENTION'::note_category_enum, 'Plano de intervenção prática iniciado após divergência entre autoavaliação e tolerância atingida no eixo escalonado.', TRUE, DATE '2026-04-10'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN users a ON a.email = 'instrutor.oficina.demo@senai.nexa.local'
WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET visibility_scope = EXCLUDED.visibility_scope, note_content = EXCLUDED.note_content, requires_followup = EXCLUDED.requires_followup, followup_date = EXCLUDED.followup_date;

INSERT INTO pedagogical_notes (id, student_id, enrollment_id, author_id, visibility_scope, category, note_content, requires_followup, followup_date)
SELECT '53000000-0000-4000-8000-000000000002'::uuid, u.id, e.id, a.id, 'COORDINATION_ONLY'::note_visibility_scope_enum, 'ACCOMMODATION'::note_category_enum, 'Acompanhamento de frequência com empresa parceira SENAI para adequação de horário sem prejuízo pedagógico.', TRUE, DATE '2026-09-25'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN users a ON a.email = 'coordenacao.demo@senai.nexa.local'
WHERE u.email = 'estudante.demo29@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET visibility_scope = EXCLUDED.visibility_scope, note_content = EXCLUDED.note_content, requires_followup = EXCLUDED.requires_followup, followup_date = EXCLUDED.followup_date;

-- 4. Mensagens Privadas em Chamados de Apoio (chat_messages — DB-044)
INSERT INTO chat_messages (id, help_request_id, sender_id, message_body, is_read, read_at, sent_at)
SELECT '54000000-0000-4000-8000-000000000001'::uuid, '52000000-0000-4000-8000-000000000001'::uuid, u.id, 'Professor, posso passar amanhã às 13h30 na oficina para treinar o zeramento da ferramenta no contraponto?', TRUE, TIMESTAMPTZ '2026-03-19T14:05:00Z', TIMESTAMPTZ '2026-03-19T13:50:00Z'
FROM users u WHERE u.email = 'estudante.demo03@aluno.nexa.local'
ON CONFLICT (id) DO UPDATE
SET is_read = EXCLUDED.is_read, read_at = EXCLUDED.read_at;

INSERT INTO chat_messages (id, help_request_id, sender_id, message_body, is_read, read_at, sent_at)
SELECT '54000000-0000-4000-8000-000000000002'::uuid, '52000000-0000-4000-8000-000000000001'::uuid, u.id, 'Combinado! Separei o Torno 04 para revisarmos juntos a centragem com calços e o faceamento passo a passo.', FALSE, NULL, TIMESTAMPTZ '2026-03-19T14:12:00Z'
FROM users u WHERE u.email = 'instrutor.oficina.demo@senai.nexa.local'
ON CONFLICT (id) DO UPDATE
SET is_read = EXCLUDED.is_read, read_at = EXCLUDED.read_at;

INSERT INTO chat_messages (id, help_request_id, sender_id, message_body, is_read, read_at, sent_at)
SELECT '54000000-0000-4000-8000-000000000003'::uuid, '52000000-0000-4000-8000-000000000002'::uuid, u.id, 'Ótima evolução na bateria de leituras de hoje! Todas as 10 medições ficaram dentro de ±0,01mm.', TRUE, TIMESTAMPTZ '2026-03-15T16:40:00Z', TIMESTAMPTZ '2026-03-15T16:20:00Z'
FROM users u WHERE u.email = 'instrutor.teoria.demo@senai.nexa.local'
ON CONFLICT (id) DO UPDATE
SET is_read = EXCLUDED.is_read, read_at = EXCLUDED.read_at;

-- 5. Catálogo Transparente de Conquistas SENAI (gamification_badges — DB-045)
INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)
SELECT 'BADGE-METROLOGIA-100', 'Mestre do Micrômetro', 'Domínio comprovado na leitura centesimal com micrômetro externo e inspeção dimensional H7.', 'Alcançar nível verificado >= 4.50 nas competências de Paquímetro ou Micrômetro em avaliações práticas validadas pelo instrutor.', 'micrometer-precision', 150, cp.id, TRUE FROM (SELECT 1) AS _seed LEFT JOIN competencies cp ON cp.code = 'COMP-MET-02'
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;

INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)
SELECT 'BADGE-PAQUIMETRO-PRO', 'Olho de Precisão H7', 'Excelência no uso de paquímetro universal com resolução 0,02mm sem desvios de leitura.', 'Concluir a tarefa prática de Inspeção Dimensional com nota >= 9.00 e evidência verificada na competência COMP-MET-01.', 'caliper-check', 120, cp.id, TRUE FROM (SELECT 1) AS _seed LEFT JOIN competencies cp ON cp.code = 'COMP-MET-01'
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;

INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)
SELECT 'BADGE-TORNEARIA-EXACT', 'Especialista em Tornearia Cilíndrica', 'Usinagem de eixo escalonado dentro da tolerância ±0,02mm e acabamento conforme desenho técnico.', 'Atingir nível >= 4 em todos os critérios técnicos da rubrica de Torneamento Cilíndrico Externo (COMP-USI-02).', 'lathe-master', 200, cp.id, TRUE FROM (SELECT 1) AS _seed LEFT JOIN competencies cp ON cp.code = 'COMP-USI-02'
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;

INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)
SELECT 'BADGE-SEGURANCA-NR12', 'Guardião NR-12 & 5S', 'Conduta exemplar de segurança industrial, bloqueio LOTO, uso integral de EPIs e bancada 5S.', 'Manter 100% de conformidade nos checklists de EPI e segurança NR-12 em todas as práticas avaliadas do semestre.', 'shield-nr12', 180, cp.id, TRUE FROM (SELECT 1) AS _seed LEFT JOIN competencies cp ON cp.code = 'COMP-SEG-01'
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;

INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)
VALUES ('BADGE-ASSIDUIDADE-100', 'Presença de Aço 100%', 'Assiduidade integral em aulas teóricas e oficinas práticas durante todo o módulo.', 'Registrar 100% de presença efetiva (zero faltas não justificadas) em todas as aulas ministradas do ciclo.', 'calendar-medal', 100, NULL, TRUE)
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;

INSERT INTO gamification_badges (code, title, description, criteria_explanation, icon_name, xp_reward, competency_id, is_active)
VALUES ('BADGE-AUTOCONHECIMENTO-360', 'Calibração Metacognitiva', 'Alinhamento consistente entre autoavaliação discente e evidências práticas verificadas.', 'Responder aos formulários de autoavaliação dentro do prazo com discrepância absoluta <= 0.50 frente à avaliação docente.', 'compass-aligned', 130, NULL, TRUE)
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title, description = EXCLUDED.description, criteria_explanation = EXCLUDED.criteria_explanation, icon_name = EXCLUDED.icon_name, xp_reward = EXCLUDED.xp_reward, is_active = EXCLUDED.is_active;

-- 6. Conquistas Desbloqueadas pelos Estudantes (student_achievements — DB-046)
INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)
SELECT u.id, e.id, b.id, TIMESTAMPTZ '2026-02-22T18:00:00Z', 'Tarefa: Inspeção Dimensional de Pino Calibrado (Nota 9.60)'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN gamification_badges b ON b.code = 'BADGE-PAQUIMETRO-PRO'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (student_id, badge_id) DO UPDATE
SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;

INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)
SELECT u.id, e.id, b.id, TIMESTAMPTZ '2026-03-02T17:15:00Z', 'Módulo 02: Metrologia com Micrômetro (Nível verificado 4.90)'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN gamification_badges b ON b.code = 'BADGE-METROLOGIA-100'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (student_id, badge_id) DO UPDATE
SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;

INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)
SELECT u.id, e.id, b.id, TIMESTAMPTZ '2026-03-26T20:00:00Z', 'Ciclo 2026.1: 25h/25h (100.00% de presença)'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN gamification_badges b ON b.code = 'BADGE-ASSIDUIDADE-100'
WHERE u.email = 'estudante.demo01@aluno.nexa.local'
ON CONFLICT (student_id, badge_id) DO UPDATE
SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;

INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)
SELECT u.id, e.id, b.id, TIMESTAMPTZ '2026-03-24T19:10:00Z', 'Tarefa: Usinagem de Eixo Escalonado Ø25mm (Nível 5)'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-1' AND cl.period = '2026.1'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN gamification_badges b ON b.code = 'BADGE-TORNEARIA-EXACT'
WHERE u.email = 'estudante.demo02@aluno.nexa.local'
ON CONFLICT (student_id, badge_id) DO UPDATE
SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;

INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)
SELECT u.id, e.id, b.id, TIMESTAMPTZ '2026-09-08T18:30:00Z', 'Oficina Integrada SENAI: 100% conformidade EPI/NR-12'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN gamification_badges b ON b.code = 'BADGE-SEGURANCA-NR12'
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (student_id, badge_id) DO UPDATE
SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;

INSERT INTO student_achievements (student_id, enrollment_id, badge_id, unlocked_at, origin_reference)
SELECT u.id, e.id, b.id, TIMESTAMPTZ '2026-09-15T19:00:00Z', 'Diagnóstico 360° Alinhado (gap 0.10)'
FROM users u
JOIN classes cl ON cl.code = 'MEC-2026-2' AND cl.period = '2026.2'
JOIN enrollments e ON e.student_id = u.id AND e.class_id = cl.id
JOIN gamification_badges b ON b.code = 'BADGE-AUTOCONHECIMENTO-360'
WHERE u.email = 'estudante.demo04@aluno.nexa.local'
ON CONFLICT (student_id, badge_id) DO UPDATE
SET unlocked_at = EXCLUDED.unlocked_at, origin_reference = EXCLUDED.origin_reference;

COMMIT;
