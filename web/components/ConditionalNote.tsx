// artifact conditional_on array → on-page provenance line (ledger logic §07)
export default function ConditionalNote({ conditional }: { conditional: string[] }) {
  if (!conditional?.length) {
    return (
      <p className="conditional-note conditional-note--proven">
        proven — invariant to λ · p_bind (Prop 1)
      </p>
    );
  }
  return (
    <p className="conditional-note conditional-note--conditional">
      conditional on: {conditional.join(", ")} (assumed)
    </p>
  );
}
