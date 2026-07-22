import Link from "next/link";
import { theorySlugs } from "../../lib/data";

export default function TheoryIndex() {
  return (
    <>
      <h1>Theory</h1>
      <p style={{ maxWidth: 720 }}>
        이론 문서의 계산값은 모델 출력에서 라이브 주입된다 — 모델을 다시 돌리면 본문
        숫자가 자동으로 따라온다 (PLAN §4.2).
      </p>
      <ul>
        {theorySlugs().map((s) => (
          <li key={s}>
            <Link href={`/theory/${s}`}>{s}</Link>
          </li>
        ))}
      </ul>
    </>
  );
}
