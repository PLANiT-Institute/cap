// calibration status flows unchanged from the pricing sheet to the UI
export default function StatusBadge({ status }: { status: string }) {
  const label = status === "assumed" ? "assumed · conditional" : status;
  return <span className={`badge badge--${status}`}>{label}</span>;
}
