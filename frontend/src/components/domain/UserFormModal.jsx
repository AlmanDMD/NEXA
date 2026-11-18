import React, { useEffect, useRef, useState } from 'react';
import { Modal, OutlineButton } from '../ui-primitives';

export function UserFormModal({ open, onClose, onSave, editingUser = null, existingEmails = [] }) {
  const firstInputRef = useRef(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [registration, setRegistration] = useState('');
  const [role, setRole] = useState('Professor');
  const [phone, setPhone] = useState('');
  const [generateTempPassword, setGenerateTempPassword] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      if (editingUser) {
        setName(editingUser.name || '');
        setEmail(editingUser.email || '');
        setRegistration(editingUser.registration || '');
        setRole(editingUser.role || 'Professor');
        setPhone(editingUser.phone || '');
      } else {
        setName('');
        setEmail('');
        setRegistration('');
        setRole('Professor');
        setPhone('');
        setGenerateTempPassword(true);
      }
      setError('');
      setTimeout(() => {
        if (firstInputRef.current) {
          firstInputRef.current.focus();
        }
      }, 50);
    }
  }, [open, editingUser]);

  const handleSubmit = (event) => {
    event.preventDefault();
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail.includes('@') || !cleanEmail.includes('senai')) {
      setError('Informe um e-mail institucional válido do domínio SENAI (ex: nome@senai-es.org.br).');
      return;
    }
    const isDuplicate = existingEmails.some(
      (e) => e.toLowerCase() === cleanEmail && (!editingUser || editingUser.email.toLowerCase() !== cleanEmail),
    );
    if (isDuplicate) {
      setError('Já existe um usuário cadastrado com este e-mail institucional.');
      return;
    }

    setSaving(true);
    setTimeout(() => {
      onSave({
        id: editingUser ? editingUser.id : `u-${Date.now()}`,
        name: name.trim(),
        email: cleanEmail,
        registration: registration.trim() || (role === 'Professor' ? 'DOC-2024.099' : '2024.0888'),
        role,
        phone: phone.trim() || '(28) 99900-0000',
        status: editingUser ? editingUser.status : 'Ativo',
        tempPasswordGenerated: generateTempPassword,
      });
      setSaving(false);
      onClose();
    }, 200);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editingUser ? `Editar usuário · ${editingUser.name}` : 'Cadastrar novo usuário'}
      subtitle="Defina os dados institucionais e o perfil de acesso (Professor ou Aluno)."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-xs font-bold text-slate-700">
          Nome completo
          <input
            ref={firstInputRef}
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex: Rafael Moreira"
            className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            data-testid="input-user-modal-name"
          />
        </label>

        <label className="block text-xs font-bold text-slate-700">
          E-mail institucional SENAI
          <input
            required
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError('');
            }}
            placeholder="nome.sobrenome@senai-es.org.br"
            className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            data-testid="input-user-modal-email"
          />
          {error && <span className="mt-1 block text-[11px] font-semibold text-red-600">{error}</span>}
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-xs font-bold text-slate-700">
            Matrícula SENAI
            <input
              required
              value={registration}
              onChange={(e) => setRegistration(e.target.value)}
              placeholder="Ex: DOC-2024.015 ou 2024.0410"
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
              data-testid="input-user-modal-registration"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Papel institucional
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-normal outline-none focus:border-sky-500"
              data-testid="select-user-modal-role"
            >
              <option value="Professor">Professor</option>
              <option value="Aluno">Aluno</option>
            </select>
          </label>
        </div>

        <label className="block text-xs font-bold text-slate-700">
          Telefone de contato
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="(28) 99999-0000"
            className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm font-normal outline-none focus:border-sky-500"
            data-testid="input-user-modal-phone"
          />
        </label>

        {!editingUser && (
          <label className="flex cursor-pointer items-center gap-2 rounded-xl bg-slate-50 p-3 text-xs text-slate-700">
            <input
              type="checkbox"
              checked={generateTempPassword}
              onChange={(e) => setGenerateTempPassword(e.target.checked)}
              className="h-4 w-4 accent-[#214d75]"
              data-testid="checkbox-user-temp-password"
            />
            Gerar senha temporária automática e enviar convite por e-mail institucional
          </label>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <OutlineButton onClick={onClose}>Cancelar</OutlineButton>
          <OutlineButton type="submit" tone="primary" testId="button-save-user-modal">
            {saving ? 'Salvando...' : editingUser ? 'Salvar alterações' : 'Cadastrar usuário'}
          </OutlineButton>
        </div>
      </form>
    </Modal>
  );
}
