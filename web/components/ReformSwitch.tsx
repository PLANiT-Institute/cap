"use client";
// The signature moment: one switch reprices carbon-policy reform and the whole
// results layer moves — CSS width transitions, no chart library.
import { useState } from "react";
import tokens from "../tokens.json";

const DRIVERS = ["carbon", "h2", "elec", "capex"] as const;
const LABELS: Record<string, string> = {
  carbon: "Carbon policy",
  h2: "Hydrogen",
  elec: "Electricity",
  capex: "Capital",
};

type Firm = {
  firm_id: string;
  firm: string;
  cluster: string;
  shares: Record<string, number>;
  shares_reform: Record<string, number>;
  premium_bps: number;
  premium_reform_bps: number;
};

export default function ReformSwitch({
  firms,
  sigmaBase,
  sigmaReform,
}: {
  firms: Firm[];
  sigmaBase: number;
  sigmaReform: number;
}) {
  const [reform, setReform] = useState(false);
  const colors = tokens.drivers as Record<string, string>;

  return (
    <div>
      <div className="switch-row">
        <div className="switch" role="group" aria-label="Carbon policy pricing regime">
          <button className={!reform ? "active" : ""} onClick={() => setReform(false)}>
            reform unpriced
          </button>
          <button className={reform ? "active active--reform" : ""} onClick={() => setReform(true)}>
            price the reform
          </button>
        </div>
        <div className="sigma-readout">
          σ<sub>carbon</sub> = <b>{(reform ? sigmaReform : sigmaBase).toFixed(2)}</b>
          {reform ? " — diffusion + policy-jump mix (MSR · CBAM scenarios)" : " — diffusion only (KAU, measured)"}
        </div>
      </div>

      <div className="firm-bars">
        {firms.map((f) => {
          const shares = reform ? f.shares_reform : f.shares;
          const bps = reform ? f.premium_reform_bps : f.premium_bps;
          return (
            <div key={f.firm_id}>
              <div className="firm-bar__head">
                <span className="firm-bar__name">
                  {f.firm}{" "}
                  <span style={{ color: "#94a3b8", fontWeight: 400, fontSize: 12 }}>
                    {f.cluster === "h2_route" ? "· short the hydrogen economy" : "· short the grid transition"}
                  </span>
                </span>
                <span className="firm-bar__meta">{bps.toFixed(1)} bps (conditional)</span>
              </div>
              <div className="firm-bar__track">
                {DRIVERS.map((d) => {
                  const w = shares[d] * 100;
                  return (
                    <div key={d} className="firm-bar__seg" style={{ width: `${w}%`, background: colors[d] }}>
                      <span>{w >= 9 ? `${LABELS[d]} ${w.toFixed(0)}%` : w >= 4 ? `${w.toFixed(0)}%` : ""}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="legend">
        {DRIVERS.map((d) => (
          <span key={d}>
            <i style={{ background: colors[d] }} /> {LABELS[d]}
          </span>
        ))}
        <span className="conditional-note conditional-note--proven" style={{ marginLeft: "auto" }}>
          composition proven — invariant to λ · p_bind (Prop 1)
        </span>
      </div>
    </div>
  );
}
