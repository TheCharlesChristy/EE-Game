interface ToastProps {
  message: string | null;
  error: string | null;
  onDismiss: () => void;
}

export function Toast({ message, error, onDismiss }: ToastProps) {
  if (!message && !error) return null;
  return (
    <div className={`toast ${error ? 'toast-error' : ''}`} role="status">
      <span>{error ?? message}</span>
      <button type="button" aria-label="Dismiss notification" onClick={onDismiss}>Dismiss</button>
    </div>
  );
}
