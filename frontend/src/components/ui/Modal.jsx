import React from 'react';
import { Modal as BaseModal, OutlineButton } from '../ui-primitives';

export { BaseModal as Modal };

export function ConfirmDialog({ open, onClose, onConfirm, title, description, confirmLabel = 'Confirmar' }) {
  return (
    <BaseModal open={open} onClose={onClose} title={title} subtitle={description}>
      <div className="mt-4 flex justify-end gap-2">
        <OutlineButton onClick={onClose}>Cancelar</OutlineButton>
        <OutlineButton
          tone="primary"
          onClick={() => {
            if (onConfirm) onConfirm();
            onClose();
          }}
        >
          {confirmLabel}
        </OutlineButton>
      </div>
    </BaseModal>
  );
}
