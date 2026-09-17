import type {
  AssessmentResponse,
  Association,
  Detection,
  VerificationIssue,
} from "./types";

/**
 * How a damage detection relates to the vehicle parts returned by the pipeline.
 *
 * - `linked`: the association names a part present in `part_detections`.
 * - `unmatched`: an association exists, but the matcher returned no part.
 * - `no_record`: no association record was returned for this damage.
 * - `unresolved_part`: the association names a part id that is not in
 *   `part_detections`, so no part can be shown.
 */
export type AssociationState = "linked" | "unmatched" | "no_record" | "unresolved_part";

export interface ResolvedAlternative {
  partId: string;
  /** Null when the alternative references a part id absent from `part_detections`. */
  part: Detection | null;
  score: number;
  /** True when this alternative's score equals the leading association score. */
  tiedWithLeader: boolean;
}

export interface DamageFinding {
  damage: Detection;
  association: Association | null;
  state: AssociationState;
  /** Only set when `state` is `linked`. */
  part: Detection | null;
  /** The association score returned by the matcher (box coverage), when an association exists. */
  score: number | null;
  alternatives: ResolvedAlternative[];
  /** Verification issues whose path refers to this damage or its association. */
  issues: VerificationIssue[];
  /** Set only when the verification layer itself reported an ambiguous association. */
  flaggedAmbiguous: boolean;
}

export interface PartFinding {
  part: Detection;
  /** Damage ids whose association names this part as the leading match. */
  linkedDamageIds: string[];
  issues: VerificationIssue[];
}

export interface ResolvedFindings {
  damages: DamageFinding[];
  parts: PartFinding[];
  linkedCount: number;
}

const TIE_TOLERANCE = 1e-9;

/**
 * Verification paths refer to a record either by list position
 * ("associations.0") or by detection id ("associations.d1"), so both forms
 * are accepted.
 */
function pathRefersTo(path: string | null, root: string, index: number, id: string): boolean {
  if (!path) return false;
  const [pathRoot, segment] = path.split(".");
  return pathRoot === root && (segment === String(index) || segment === id);
}

/**
 * Resolve the references between damage detections, part detections and
 * associations exactly as returned by the backend. Nothing is inferred: a
 * damage without a resolvable part association is reported as such.
 */
export function resolveFindings(result: AssessmentResponse): ResolvedFindings {
  const { damage_detections, part_detections, associations } = result.cv_output;
  const issues = result.verification.issues;
  const partById = new Map(part_detections.map((part) => [part.id, part]));

  const damages = damage_detections.map((damage, damageIndex): DamageFinding => {
    const associationIndex = associations.findIndex((item) => item.damage_id === damage.id);
    const association = associationIndex >= 0 ? associations[associationIndex] : null;

    let state: AssociationState;
    let part: Detection | null = null;
    if (!association) {
      state = "no_record";
    } else if (association.part_id === null) {
      state = "unmatched";
    } else {
      part = partById.get(association.part_id) ?? null;
      state = part ? "linked" : "unresolved_part";
    }

    const alternatives = (association?.alternatives ?? []).map((alternative) => ({
      partId: alternative.part_id,
      part: partById.get(alternative.part_id) ?? null,
      score: alternative.confidence,
      tiedWithLeader:
        association !== null && Math.abs(alternative.confidence - association.confidence) < TIE_TOLERANCE,
    }));

    const findingIssues = issues.filter(
      (issue) =>
        pathRefersTo(issue.path, "damage_detections", damageIndex, damage.id) ||
        (associationIndex >= 0 && pathRefersTo(issue.path, "associations", associationIndex, damage.id)),
    );

    return {
      damage,
      association,
      state,
      part,
      score: association ? association.confidence : null,
      alternatives,
      issues: findingIssues,
      flaggedAmbiguous: findingIssues.some((issue) => issue.code === "ambiguous_part_association"),
    };
  });

  const parts = part_detections.map((part, partIndex): PartFinding => ({
    part,
    linkedDamageIds: damages
      .filter((finding) => finding.state === "linked" && finding.part?.id === part.id)
      .map((finding) => finding.damage.id),
    issues: issues.filter((issue) => pathRefersTo(issue.path, "part_detections", partIndex, part.id)),
  }));

  return {
    damages,
    parts,
    linkedCount: damages.filter((finding) => finding.state === "linked").length,
  };
}
