"use client";
// recharts는 클라이언트 전용 — 데이터는 서버 컴포넌트에서 props로 내려온다 (계산 없음)
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ErrorBar,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "capex"] as const;
const DRIVER_KO: Record<string, string> = {
  carbon: "Carbon",
  h2: "Hydrogen",
  elec: "Electricity",
  capex: "Capital",
};
const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export function SharesStackedBar({
  rows,
}: {
  rows: { name: string; cluster: string; [k: string]: number | string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={rows} stackOffset="expand" margin={{ top: 8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={tokens.palette.slateLight} />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number, n: string) => [pct(v), DRIVER_KO[n] ?? n]} />
        <Legend formatter={(n: string) => DRIVER_KO[n] ?? n} />
        {DRIVERS.map((d) => (
          <Bar key={d} dataKey={d} stackId="s" fill={(tokens.drivers as any)[d]} isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function WedgeDumbbell({
  rows,
  equalized,
}: {
  rows: { asset: string; t_gcam: number; tau_star: number | null; tau_star_eq: number | null }[];
  equalized: boolean;
}) {
  const gcamPts = rows.map((r) => ({ x: r.t_gcam, y: r.asset }));
  const tauPts = rows
    .map((r) => ({ x: equalized ? r.tau_star_eq : r.tau_star, y: r.asset }))
    .filter((p) => p.x != null);
  return (
    <ResponsiveContainer width="100%" height={420}>
      <ScatterChart margin={{ top: 8, right: 16, left: 48 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={tokens.palette.slateLight} />
        <XAxis
          type="number"
          dataKey="x"
          domain={["dataMin - 2", "dataMax + 2"]}
          tickFormatter={(v) => String(Math.round(v))}
          tick={{ fontSize: 12 }}
        />
        <YAxis type="category" dataKey="y" width={110} tick={{ fontSize: 11 }} allowDuplicatedCategory={false} />
        <Tooltip formatter={(v: number) => v?.toFixed?.(1)} />
        <Legend />
        <Scatter name="T_GCAM (required)" data={gcamPts} fill={tokens.palette.accent} isAnimationActive={false} />
        <Scatter name="τ* (private optimum)" data={tauPts} fill={tokens.palette.navy} isAnimationActive={false} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function WaterfallBars({
  steps,
}: {
  steps: { label: string; premium_bps: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={steps} margin={{ top: 8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={tokens.palette.slateLight} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} />
        <YAxis tick={{ fontSize: 12 }} label={{ value: "bps", angle: -90, position: "insideLeft" }} />
        <Tooltip formatter={(v: number) => `${v.toFixed(1)} bps`} />
        <Bar dataKey="premium_bps" isAnimationActive={false}>
          {steps.map((s, i) => (
            <Cell key={i} fill={i === 0 ? tokens.palette.red : tokens.palette.navy} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function EnvelopeBars({
  rows,
}: {
  rows: { driver: string; median: number; lo: number; hi: number }[];
}) {
  const data = rows.map((r) => ({
    ...r,
    label: DRIVER_KO[r.driver] ?? r.driver,
    err: [r.median - r.lo, r.hi - r.median],
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={tokens.palette.slateLight} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => pct(v)} />
        <Bar dataKey="median" fill={tokens.palette.navy} isAnimationActive={false}>
          <ErrorBar dataKey="err" stroke={tokens.palette.accent} width={6} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
