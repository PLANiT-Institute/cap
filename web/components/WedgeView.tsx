"use client";
import { useState } from "react";
import { WedgeDumbbell } from "./charts";

export default function WedgeView({ rows }: { rows: any[] }) {
  const [eq, setEq] = useState(false);
  return (
    <>
      <label style={{ fontSize: 14 }}>
        <input type="checkbox" checked={eq} onChange={(e) => setEq(e.target.checked)} />{" "}
        WACC-equalized (R4 순환성 부분 대응)
      </label>
      <WedgeDumbbell rows={rows} equalized={eq} />
    </>
  );
}
