#!/usr/bin/env bash
# compile_oracle.sh — compile oracle for the 17 disputed genesis-vibes transitions (wild-150)
#
# Pre-registration (anti-goal compliance): the 17 disputed (provider_from -> provider_to)
# transitions below were enumerated BEFORE any compile run, using the recorded method of
# experiments/run_rust.py over all 120 genesis-vibes version pairs (contract shape_check via
# prototype/wild_proto.extract_rust vs the Cargo 0.x caret rule). Counts match RESULTS.md §1:
# 14 Cargo-incompatible-but-accretion + 3 Cargo-compatible-but-break. Do not edit the table
# after seeing compile outcomes.
#
# Semantics (per brief, not invented): for each disputed transition and each consumer tag
# whose demand allows provider_to (RESULTS.md §1 demand lines), record
#   probe   = consumer compiles against provider_to   (compiles => break missed or contract right)
#   control = consumer compiles against provider_from (sanity)
# Demand-allowed set per tag = its Cargo caret range ∪ the beyond-range versions recorded in
# RESULTS.md §1. Transitions with no consumer demand are recorded N/A with the reason.
#
# Scratch lives under /tmp/co (never committed). Provider sources: /tmp/proj/gv/<ver>
# (fetched from static.crates.io if absent). Consumer sources: detached git worktrees
# /tmp/spk-<tag> of the specodelic repo (READ-ONLY; copies are compiled, never the repo).
#
# Output: verdict table on stdout and experiments/compile_oracle_results.txt.
# Exit 0 = all cells recorded (a consumer compile failure is a verdict, not an error);
# exit 1 = infrastructure failure (fetch/worktree/cargo missing).

set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/experiments/compile_oracle_results.txt"
SCRATCH="${COMPILE_ORACLE_SCRATCH:-/tmp/co}"
GV_ROOT="/tmp/proj/gv"
SPK_SRC="${SPECODELIC_DIR:-/var/home/sasha/para/areas/dev/gh/charly/specodelic}"
CRATE_URL="https://static.crates.io/crates/genesis-vibes/genesis-vibes-<ver>.crate"

GV_VERSIONS="0.2.0 0.3.0 0.4.0 0.5.0 0.6.0 0.7.0 0.8.0 0.8.1 0.8.2 0.8.3 0.9.0 0.10.0 0.10.1 0.11.0 0.11.1 0.12.0"
SPK_TAGS="v0.1.0 v0.2.0 v0.3.0 v0.4.0 v0.5.0"

# Pre-registered 17 disputed transitions (from -> to).
# Applicable consumer tags = demand-allowed(provider_to) per RESULTS.md §1 demand lines:
#   v0.1.0: {0.7.0} + beyond {0.8.0}
#   v0.2.0: {0.8.0..0.8.3} + beyond {0.9.0,0.10.0,0.10.1,0.11.0,0.11.1,0.12.0}
#   v0.3.0: {0.10.0,0.10.1} + beyond {0.11.0,0.11.1,0.12.0}
#   v0.4.0: {0.11.0,0.11.1} + beyond {0.12.0}
#   v0.5.0: {0.11.0,0.11.1} + beyond {0.12.0}
# (transitions 0.8.x -> 0.9.0 applied to 0.8.1/0.8.2/0.8.3 froms too: each from is in
#  v0.2.0's caret range; the pair's to must be demand-allowed.)
TRANSITIONS=(
  "0.8.0->0.8.1|v0.2.0"
  "0.8.0->0.8.2|v0.2.0"
  "0.8.0->0.8.3|v0.2.0"
  "0.8.1->0.9.0|v0.2.0"
  "0.8.2->0.9.0|v0.2.0"
  "0.8.3->0.9.0|v0.2.0"
  "0.10.0->0.11.0|v0.2.0 v0.3.0"
  "0.10.0->0.11.1|v0.2.0 v0.3.0"
  "0.10.1->0.11.0|v0.2.0 v0.3.0"
  "0.10.1->0.11.1|v0.2.0 v0.3.0"
  "0.10.0->0.12.0|v0.2.0 v0.3.0 v0.4.0 v0.5.0"
  "0.10.1->0.12.0|v0.2.0 v0.3.0 v0.4.0 v0.5.0"
  "0.11.0->0.12.0|v0.2.0 v0.3.0 v0.4.0 v0.5.0"
  "0.11.1->0.12.0|v0.2.0 v0.3.0 v0.4.0 v0.5.0"
  "0.3.0->0.4.0|"
  "0.3.0->0.5.0|"
  "0.4.0->0.5.0|"
)

die() { echo "FATAL: $*" >&2; exit 1; }

command -v cargo >/dev/null || die "cargo not found"
command -v rustc >/dev/null || die "rustc not found"

# ---- toolchain record (pinned into output) ----
CARGO_VER="$(cargo --version)"
RUSTC_VER="$(rustc --version)"

# ---- provider sources ----
mkdir -p "$GV_ROOT"
for v in $GV_VERSIONS; do
  if [ ! -f "$GV_ROOT/$v/Cargo.toml" ]; then
    url="${CRATE_URL/<ver>/$v}"
    curl -sSfL --max-time 60 -o "$GV_ROOT/gv-$v.crate" "$url" \
      || die "crates.io unreachable: failed to fetch $url (record as BLOCKED; do not fabricate)"
    mkdir -p "$GV_ROOT/$v"
    tar xzf "$GV_ROOT/gv-$v.crate" -C "$GV_ROOT/$v" --strip-components=1 || die "untar failed for $v"
    rm -f "$GV_ROOT/gv-$v.crate"
  fi
done

# ---- consumer worktrees (READ-ONLY repo: only detached worktrees under /tmp) ----
for t in $SPK_TAGS; do
  if [ ! -f "/tmp/spk-$t/Cargo.toml" ]; then
    git -C "$SPK_SRC" worktree add --detach "/tmp/spk-$t" "$t" >/dev/null 2>&1 \
      || die "worktree add failed for $t (repo: $SPK_SRC)"
  fi
done

# ---- cell cache: compile (tag, version) once ----
CACHE_DIR="$SCRATCH/cache"
mkdir -p "$SCRATCH" "$CACHE_DIR"

run_cell() {  # $1=tag $2=version  -> sets CELL_EXIT, CELL_ERR
  local tag="$1" ver="$2"
  local cf="$CACHE_DIR/${tag}_${ver}"
  if [ -f "$cf.exit" ]; then
    CELL_EXIT="$(cat "$cf.exit")"; CELL_ERR="$(cat "$cf.err")"; return 0
  fi
  local dst="$SCRATCH/$tag"
  rm -rf "$dst"
  cp -r "/tmp/spk-$tag" "$dst" || { CELL_EXIT=infra; CELL_ERR="copy failed"; return 0; }
  # pin genesis-vibes exactly; preserve the features table form if present
  ( cd "$dst" \
    && sed -i -e "s/^genesis-vibes = \"[^\"]*\"/genesis-vibes = \"=$ver\"/" \
              -e "s/^genesis-vibes = { version = \"[^\"]*\"/genesis-vibes = { version = \"=$ver\"/" Cargo.toml )
  grep -q "genesis-vibes = .*=$ver" "$dst/Cargo.toml" \
    || { CELL_EXIT=infra; CELL_ERR="pin edit failed"; return 0; }
  local log
  log="$(cd "$dst" && CARGO_TARGET_DIR="$SCRATCH/target" cargo check 2>&1)"
  CELL_EXIT=$?
  CELL_ERR="$(printf '%s\n' "$log" | grep -oE 'error\[[A-Z0-9]+\].*' | head -1 | cut -c1-80)"
  [ -z "$CELL_ERR" ] && [ "$CELL_EXIT" -ne 0 ] && CELL_ERR="(non-E-coded compile error)"
  printf '%s' "$CELL_EXIT" > "$cf.exit"; printf '%s' "$CELL_ERR" > "$cf.err"
  return 0
}

verdict() {  # $1=exit code -> human verdict
  case "$1" in
    0) echo "PASS";;
    101) echo "FAIL";;
    *) echo "FAIL(exit=$1)";;
  esac
}

# ---- run ----
{
  echo "# compile oracle — genesis-vibes (provider) × specodelic (consumer), disputed transitions"
  echo "# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# toolchain: $CARGO_VER | $RUSTC_VER"
  echo "# method: probe = consumer pinned (=\"provider_to\") compiles? control = consumer pinned (=\"provider_from\")."
  echo "#         Applicability = RESULTS.md §1 demand lines (cargo caret range ∪ beyond-range demand)."
  echo "transition|consumer_tag|provider_pair|probe(to)|control(from)|first_error|toolchain"
} > "$OUT"

printf 'compile oracle — genesis-vibes × specodelic disputed transitions\n'
printf 'toolchain: %s | %s\n\n' "$CARGO_VER" "$RUSTC_VER"

FAILCOUNT=0
for row in "${TRANSITIONS[@]}"; do
  pair="${row%%|*}"; tags="${row#*|}"
  from="${pair%%->*}"; to="${pair##*->}"
  if [ -z "$tags" ]; then
    line="$pair|—|N/A|N/A|N/A|no consumer tag demands provider_to (RESULTS.md §1 demand lines: earliest consumer v0.1.0 demands 0.7; 0.4.0/0.5.0 allowed by no tag)|-"
    echo "$line" >> "$OUT"; printf '%s\n' "$line"; continue
  fi
  for tag in $tags; do
    run_cell "$tag" "$to";   p_exit=$CELL_EXIT; p_err=$CELL_ERR
    run_cell "$tag" "$from"; c_exit=$CELL_EXIT; c_err=$CELL_ERR
    [ "$p_exit" = "infra" ] || [ "$c_exit" = "infra" ] && die "infrastructure failure in cell $tag ($from→$to)"
    perr="$p_err"; [ -n "$perr" ] || perr="-"
    cerr="$c_err"; [ -n "$cerr" ] || cerr="-"
    line="$pair|$tag|$from->$to|$(verdict "$p_exit")|$(verdict "$c_exit")|probe_err:$perr control_err:$cerr|$RUSTC_VER"
    echo "$line" >> "$OUT"; printf '%s\n' "$line"
  done
done

# ---- supplementary cells (NOT part of the 17; recorded for §1 demand-line honesty) ----
# v0.1.0 (declared "0.7", demand beyond-Cargo: +1 = 0.8.0 per RESULTS.md §1):
#   0.7.0  control (declared floor)
#   0.8.0  demand-allowed beyond Cargo — does the contract's +1 claim hold at source level?
#   0.8.1  outside demand — does v0.1.0's source hit the 0.8.1 struct-field break?
SUPPLEMENTARY=("v0.1.0|0.7.0" "v0.1.0|0.8.0" "v0.1.0|0.8.1")
{
  echo ""
  echo "# supplementary cells (outside the 17 disputed transitions; demand-line probes)"
  echo "supplementary_consumer|pinned_version|verdict|first_error|toolchain"
} >> "$OUT"
printf '\nsupplementary cells (outside the 17):\n'
for row in "${SUPPLEMENTARY[@]}"; do
  tag="${row%%|*}"; ver="${row##*|}"
  run_cell "$tag" "$ver"; e=$CELL_EXIT; err=$CELL_ERR
  [ "$e" = "infra" ] && die "infrastructure failure in supplementary cell $tag/$ver"
  [ -n "$err" ] || err="-"
  line="$tag|$ver|$(verdict "$e")|$err|$RUSTC_VER"
  echo "$line" >> "$OUT"; printf '%s\n' "$line"
done

echo "" >> "$OUT"
echo "# toolchain: $CARGO_VER | $RUSTC_VER" >> "$OUT"
printf '\nresults written to %s\n' "$OUT"
exit 0
}