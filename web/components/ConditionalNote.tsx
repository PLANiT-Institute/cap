// artifact의 conditional_on 배열 → 화면 경고 (원장 로직 §07)
export default function ConditionalNote({ conditional }: { conditional: string[] }) {
  if (!conditional?.length) {
    return (
      <p style={{ fontSize: 12, color: "#15803d" }}>
        proven — λ·p_bind 불진입 (Prop 1)
      </p>
    );
  }
  return (
    <p style={{ fontSize: 12, color: "#b91c1c" }}>
      conditional on: {conditional.join(", ")} (assumed)
    </p>
  );
}
