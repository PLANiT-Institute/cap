import { artifact } from "../lib/data";
import UnderwritingDashboard from "../components/UnderwritingDashboard";

export default function Home() {
  const underwriting = artifact("transition_underwriting");
  const deals = artifact("deal_screening");
  const gaps = artifact("condition_gap");
  const manifest = artifact("manifest");
  const resultContract = artifact("result_contract");
  const pilots = artifact("pilot_cases");
  const gapByFirm = new Map<string, any>(gaps.firms.map((gap: any) => [gap.firm_id, gap]));
  const data = {
    ...underwriting,
    portfolio: underwriting.portfolio.map((row: any) => ({
      ...row,
      cumulative_alignment_gap_mtco2:
        gapByFirm.get(row.firm_id)?.cumulative_alignment_gap_mtco2 ?? null,
      alignment_result_contract: gapByFirm.get(row.firm_id)?.result_contract ?? null,
    })),
  };

  return (
    <main>
      <section className="uw-head">
        <div>
          <p className="eyebrow">CAP Transition Risk Underwriter</p>
          <div className="release-banner">
            <span>{resultContract.release_stage.replaceAll("_", " ")}</span>
            <b>{pilots.capability_stage.replaceAll("_", " ")} · 40 blocked by actual cases and quotes · not cleared for external release</b>
          </div>
          <h1>The technology route <em>shapes the risk charge.</em></h1>
          <p>
            Translate an industrial technology route into its financial risk anatomy, test which
            certainty contract changes the burden, and screen whether the resulting project clears
            value, debt-service and decarbonization-depth gates. The conditional risk charge is a
            model-implied bps normalization, not an observed credit spread.
          </p>
          <p className="uw-head__meta">
            Artifact <span className="mono">{manifest.config_sha256.slice(0, 12)}</span> · {underwriting.perspective}
            {manifest.git_dirty ? " · working tree DIRTY" : ""}
          </p>
        </div>
      </section>
      <UnderwritingDashboard data={data} deals={deals} />
    </main>
  );
}
