import tokens from "../tokens.json";

// pricing 시트의 status가 그대로 UI까지 흐른다 (PLAN Phase 3-4)
export default function StatusBadge({ status }: { status: string }) {
  const color =
    (tokens.status as Record<string, string>)[status] ?? tokens.palette.slate;
  const label = status === "assumed" ? "assumed·conditional" : status;
  return (
    <span
      style={{
        backgroundColor: color,
        color: "white",
        borderRadius: 4,
        padding: "1px 6px",
        fontSize: 11,
        fontWeight: 600,
        marginLeft: 6,
        verticalAlign: "middle",
      }}
    >
      {label}
    </span>
  );
}
