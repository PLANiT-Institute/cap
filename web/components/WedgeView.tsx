"use client";
import { useState } from "react";
import { WedgeDumbbell } from "./charts";

export default function WedgeView({ rows }: { rows: any[] }) {
  const [eq, setEq] = useState(false);
  return (
    <>
      <label style={{ fontSize: 14 }}>
        <input type="checkbox" checked={eq} onChange={(e) => setEq(e.target.checked)} /> Equalize
        WACC across firms (answers the discount-rate circularity critique, R4)
      </label>
      <WedgeDumbbell rows={rows} equalized={eq} />
    </>
  );
}
