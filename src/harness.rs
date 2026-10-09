// Purpose: Sandboxed law-suite execution for authored obligations (beads
//   wild-mh5.4).
// Responsibilities: Execute a digest-bound law-suite executable against the
//   candidate artifact under an enforced sandbox — Landlock denies network
//   access and every filesystem write while confining reads to the supplied
//   base/candidate bundles and the system runtime (/usr), rlimits cap file
//   size, descriptors, processes, memory, and CPU, a fixed minimal
//   environment is handed to the child, and a wall deadline kills overruns —
//   feeding the suite a stdin invocation record {artifact, law, fixtures,
//   seed, budgets}; echo-validate the suite's v1 law_result stdout against
//   runner-derived digests (malformed or mismatching stdout is
//   runner-authored inconclusive, never an accepting result); downgrade
//   proof/exhaustive methods to inconclusive (sampled evidence only in this
//   slice); execute the suite twice and require both runs' canonical bytes
//   to match (else nondeterminism-inconclusive); and expose the enforced
//   sandbox capabilities for the report.
// Rationale: The decided semantics (interactive review D1-D10) make law
//   evidence honest by construction: a pass is only a twice-repeated,
//   echo-validated, sampled result produced under enforced isolation, and
//   every captured failure mode (unrunnable bound bytes, sandbox
//   unavailability, wall timeout, crash, echo mismatch, nondeterminism,
//   proof/exhaustive downgrade) yields inconclusive rather than a
//   fabricated success, while a genuine runner spawn failure stays an
//   operational error. The sandbox is applied with raw libc syscalls inside
//   the pre-exec hook so restriction setup is async-signal-safe and the
//   runner process itself stays unrestricted (the runner must still write
//   reports after law execution); `wild` is single-threaded when the hook
//   runs, and the stdout/stderr reader threads are joined before any later
//   spawn, keeping the post-fork state safe. Exec failures with ENOEXEC or
//   EACCES mean the bound bytes themselves cannot be run as a program, so
//   they carry no execution evidence (inconclusive); all other spawn
//   failures, including a missing interpreter (ENOENT), are runner-side
//   operational failures (error class).

use std::ffi::CString;
use std::io::{Read, Write};
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

use crate::formats::{self, Value};

/// The exact stdout record fields an executable law suite may emit.
const LAW_RESULT_FIELDS: &[&str] = &[
    "version",
    "kind",
    "law_suite",
    "contract",
    "implementation_artifact",
    "harness",
    "fixtures",
    "seed",
    "budgets",
    "method",
    "status",
    "witness",
    "reason",
];

/// Landlock syscall numbers (x86_64/aarch64 unified numbering).
const SYS_LANDLOCK_CREATE_RULESET: libc::c_long = 444;
const SYS_LANDLOCK_ADD_RULE: libc::c_long = 445;
const SYS_LANDLOCK_RESTRICT_SELF: libc::c_long = 446;
const LANDLOCK_CREATE_RULESET_VERSION: libc::c_int = 1;
const LANDLOCK_RULE_PATH_BENEATH: libc::c_int = 1;
const PR_SET_NO_NEW_PRIVS: libc::c_int = 38;
/// Not exported by this libc version for the gnu target; fixed by Linux ABI.
const O_PATH: libc::c_int = 0o10000000;
const LANDLOCK_ACCESS_FS_EXECUTE: u64 = 1 << 0;
const LANDLOCK_ACCESS_FS_READ_FILE: u64 = 1 << 2;
const LANDLOCK_ACCESS_FS_READ_DIR: u64 = 1 << 3;

/// Memory cap for law children: 512 MiB is ample for a scripting runtime.
const LAW_MEM_LIMIT: libc::rlim_t = 512 * 1024 * 1024;

/// One executed (or attempted) law's evidence for the report's
/// `law_methods` array. `status`/`method` are null when no validated
/// execution evidence was obtained.
pub struct LawOutcome {
    pub verdict: &'static str,
    pub method: Option<String>,
    pub status: Option<String>,
    pub witness: Option<String>,
    pub reason: Option<String>,
    pub result_digest: Option<String>,
    /// Runner-derived bindings the executed result must carry; null when
    /// no execution evidence was obtained.
    pub contract_digest: Option<String>,
    pub artifact_digest: Option<String>,
    pub harness_digest: Option<String>,
    pub runs: u32,
}

/// Enforced sandbox capabilities recorded in the invocation commitment.
pub struct SandboxCaps {
    pub enforced: bool,
    pub landlock_abi: Option<i64>,
}

pub fn sandbox_caps() -> SandboxCaps {
    let abi = landlock_abi_query();
    SandboxCaps {
        enforced: abi >= 1,
        landlock_abi: if abi >= 1 { Some(abi) } else { None },
    }
}

/// Probe the kernel's Landlock ABI version (0 means unavailable).
fn landlock_abi_query() -> i64 {
    unsafe {
        let ret = libc::syscall(
            SYS_LANDLOCK_CREATE_RULESET,
            std::ptr::null::<libc::c_void>(),
            0 as libc::c_uint,
            LANDLOCK_CREATE_RULESET_VERSION,
        );
        ret.max(0)
    }
}

/// Law-suite invocation inputs resolved and validated from the check
/// request by the caller.
pub struct LawInputs {
    pub harness_rel: String,
    pub harness_digest: String,
    pub fixture_files: Vec<(String, String)>,
    pub wall_ms: i64,
    pub seed: i64,
    pub evaluation_time: String,
}

/// Execute one law suite against the candidate artifact; `Ok` carries the
/// law outcome (including every inconclusive shape), `Err` is an
/// operational runner failure (error class, exit 2).
pub fn run_law(
    suite_path: &Path,
    suite_digest: &str,
    contract_digest: &str,
    artifact_root: &str,
    artifact_digest: &str,
    fixture_root: &str,
    inputs: &LawInputs,
) -> Result<LawOutcome, String> {
    // Defense in depth: the bound bytes must be what the digest names.
    let suite_bytes = std::fs::read(suite_path)
        .map_err(|e| format!("input-mismatch: law suite unreadable: {e}"))?;
    if formats::sha256_digest(&suite_bytes) != suite_digest {
        return Err(
            "input-mismatch: law suite bytes do not hash to the bound suite digest"
                .to_string(),
        );
    }
    let fixture_map = formats::obj(
        inputs
            .fixture_files
            .iter()
            .map(|(rel, digest)| (rel.as_str(), formats::s(digest)))
            .collect(),
    );
    let invocation = formats::obj(vec![
        ("version", formats::s("local-1")),
        ("kind", formats::s("law-invocation")),
        (
            "artifact",
            formats::obj(vec![
                ("root", formats::s(artifact_root)),
                ("digest", formats::s(artifact_digest)),
                ("contract", formats::s(contract_digest)),
            ]),
        ),
        (
            "law",
            formats::obj(vec![
                ("suite", formats::s(suite_digest)),
                ("harness", formats::s(&inputs.harness_digest)),
            ]),
        ),
        (
            "fixtures",
            formats::obj(vec![
                ("root", formats::s(fixture_root)),
                ("files", fixture_map),
            ]),
        ),
        ("seed", formats::i(inputs.seed)),
        (
            "budgets",
            formats::obj(vec![("wall_ms", formats::i(inputs.wall_ms))]),
        ),
    ]);
    let invocation_bytes = formats::canonical(&invocation).into_bytes();
    let expected = ExpectedEcho {
        suite_digest: suite_digest.to_string(),
        contract_digest: contract_digest.to_string(),
        artifact_digest: artifact_digest.to_string(),
        harness_digest: inputs.harness_digest.clone(),
        fixture_digests: inputs
            .fixture_files
            .iter()
            .map(|(_, d)| d.clone())
            .collect(),
        seed: inputs.seed,
        wall_ms: inputs.wall_ms,
    };

    let landlock_roots: Vec<CString> = [fixture_root, artifact_root, "/usr"]
        .iter()
        .map(|root| CString::new(*root).expect("root paths are valid UTF-8"))
        .collect();

    let first = run_once(suite_path, &invocation_bytes, &expected, &landlock_roots)?;
    let outcome = match first {
        RunResult::Unrunnable(reason) => LawOutcome {
            verdict: "law-retained-inconclusive",
            method: None,
            status: None,
            witness: None,
            reason: Some(reason),
            result_digest: None,
            contract_digest: None,
            artifact_digest: None,
            harness_digest: None,
            runs: 1,
        },
        RunResult::SandboxUnavailable(reason) => LawOutcome {
            verdict: "law-executed-inconclusive",
            method: None,
            status: None,
            witness: None,
            reason: Some(reason),
            result_digest: None,
            contract_digest: None,
            artifact_digest: None,
            harness_digest: None,
            runs: 1,
        },
        RunResult::Valid(first) => {
            let second = run_once(suite_path, &invocation_bytes, &expected, &landlock_roots)?;
            match second {
                RunResult::Valid(other) if other.canonical == first.canonical => {
                    validated_outcome(&first)
                }
                RunResult::Valid(_) => LawOutcome {
                    verdict: "law-executed-inconclusive",
                    method: None,
                    status: Some("inconclusive".to_string()),
                    witness: None,
                    reason: Some(
                        "nondeterministic suite output: the two runs did not agree on canonical law_result bytes"
                            .to_string(),
                    ),
                    result_digest: None,
                    contract_digest: None,
                    artifact_digest: None,
                    harness_digest: None,
                    runs: 2,
                },
                other => inconclusive_from("inconsistent outcomes across runs", &other),
            }
        }
        other => inconclusive_from("first run did not produce validated evidence", &other),
    };
    Ok(outcome)
}

fn validated_outcome(parsed: &ParsedResult) -> LawOutcome {
    let base = |
        verdict: &'static str,
        witness: Option<String>,
        reason: Option<String>,
    | LawOutcome {
        verdict,
        method: parsed.method.clone(),
        status: Some(parsed.status.clone()),
        witness,
        reason,
        result_digest: Some(formats::sha256_digest(parsed.canonical.as_bytes())),
        contract_digest: None,
        artifact_digest: None,
        harness_digest: None,
        runs: 2,
    };
    match parsed.status.as_str() {
        "pass" => base("law-pass", parsed.witness.clone(), None),
        "counterexample" => base("law-counterexample", parsed.witness.clone(), None),
        _ => base("law-executed-inconclusive", None, parsed.reason.clone()),
    }
}

fn inconclusive_from(fallback: &str, run: &RunResult) -> LawOutcome {
    let reason = match run {
        RunResult::Unrunnable(reason)
        | RunResult::SandboxUnavailable(reason)
        | RunResult::Inconclusive(reason) => reason.clone(),
        RunResult::Valid(_) => fallback.to_string(),
    };
    LawOutcome {
        verdict: "law-executed-inconclusive",
        method: None,
        status: Some("inconclusive".to_string()),
        witness: None,
        reason: Some(reason),
        result_digest: None,
        contract_digest: None,
        artifact_digest: None,
        harness_digest: None,
        runs: 2,
    }
}

/// The runner-derived values every suite-emitted law_result must echo.
struct ExpectedEcho {
    suite_digest: String,
    contract_digest: String,
    artifact_digest: String,
    harness_digest: String,
    fixture_digests: Vec<String>,
    seed: i64,
    wall_ms: i64,
}

/// A run's validated law_result: its canonical bytes plus the (possibly
/// downgraded) claimed fields, kept separately so D9 compares bytes while
/// the report keeps the claimed method.
struct ParsedResult {
    canonical: String,
    method: Option<String>,
    status: String,
    witness: Option<String>,
    reason: Option<String>,
}

enum RunResult {
    /// The bound bytes cannot be run as a program (no execution evidence).
    Unrunnable(String),
    /// The kernel cannot enforce the required isolation (refuse-unconfined).
    SandboxUnavailable(String),
    /// The suite ran but produced only inconclusive evidence.
    Inconclusive(String),
    /// Echo-validated law_result (method/status after downgrade rules).
    Valid(ParsedResult),
}

fn run_once(
    suite_path: &Path,
    invocation: &[u8],
    expected: &ExpectedEcho,
    landlock_roots: &[CString],
) -> Result<RunResult, String> {
    let mut command = Command::new(suite_path);
    command
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .env("LANG", "C")
        .env("LC_ALL", "C")
        .env("TZ", "UTC")
        .current_dir(
            suite_path
                .parent()
                .unwrap_or_else(|| Path::new("/")),
        )
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let expected_wall = expected.wall_ms;
    let sandbox_roots: Vec<CString> = landlock_roots.to_vec();
    unsafe {
        command.pre_exec(move || {
            apply_rlimits(expected_wall)?;
            apply_landlock(&sandbox_roots)
        });
    }
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(e) => {
            let classified = classify_spawn_error(e)?;
            return Ok(classified);
        }
    };

    // Feed the invocation record; a suite that exited already cannot read
    // it, and a broken pipe there is the suite's fault, not the runner's.
    let mut stdin = child.stdin.take().expect("piped stdin");
    let invocation_owned = invocation.to_vec();
    let stdin_writer = std::thread::spawn(move || {
        let _ = stdin.write_all(&invocation_owned);
    });
    let mut stdout_pipe = child.stdout.take().expect("piped stdout");
    let mut stderr_pipe = child.stderr.take().expect("piped stderr");
    let stdout_reader = std::thread::spawn(move || {
        let mut buf = Vec::new();
        let _ = stdout_pipe.read_to_end(&mut buf);
        buf
    });
    let stderr_reader = std::thread::spawn(move || {
        let mut buf = Vec::new();
        let _ = stderr_pipe.read_to_end(&mut buf);
        buf
    });

    // Wall deadline: the parent kills the suite at the budget; any result
    // produced at or after the deadline is discarded as inconclusive.
    let deadline = Instant::now() + Duration::from_millis(expected_wall.max(1) as u64);
    let mut timed_out = false;
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) => {
                if Instant::now() >= deadline {
                    timed_out = true;
                    let _ = child.kill();
                    break child
                        .wait()
                        .map_err(|e| format!("law runner failed to reap the suite: {e}"))?;
                }
                std::thread::sleep(Duration::from_millis(5));
            }
            Err(e) => return Err(format!("law runner failed to await the suite: {e}")),
        }
    };
    if stdin_writer.join().is_err() {
        return Err("law runner stdin writer failed".to_string());
    }
    let stdout = stdout_reader
        .join()
        .map_err(|_| "law runner stdout reader failed".to_string())?;
    let stderr_bytes = stderr_reader
        .join()
        .map_err(|_| "law runner stderr reader failed".to_string())?;

    if timed_out {
        return Ok(RunResult::Inconclusive(
            "wall budget exceeded before the suite finished; any late result is discarded"
                .to_string(),
        ));
    }
    if !status.success() {
        let stderr_note = String::from_utf8_lossy(&stderr_bytes[stderr_bytes
            .len()
            .saturating_sub(400)..])
            .lines()
            .last()
            .unwrap_or("")
            .to_string();
        return Ok(RunResult::Inconclusive(format!(
            "suite crashed with exit status {}{}",
            status.code().unwrap_or(-1),
            if stderr_note.is_empty() {
                String::new()
            } else {
                format!(": {stderr_note}")
            }
        )));
    }
    let text = match std::str::from_utf8(&stdout) {
        Ok(text) => text,
        Err(_) => {
            return Ok(RunResult::Inconclusive(
                "suite stdout is not UTF-8".to_string(),
            ));
        }
    };
    validate_result(text, expected)
}

/// Map a spawn failure: sandbox-unavailable errnos mean the child could not
/// confine itself (refuse-unconfined); ENOEXEC/EACCES mean the bound bytes
/// are not runnable as a program; anything else is an operational error.
fn classify_spawn_error(e: std::io::Error) -> Result<RunResult, String> {
    let errno = e.raw_os_error().unwrap_or(-1);
    match errno {
        libc::ENOSYS | libc::EINVAL | libc::EPERM | libc::ENOPROTOOPT | libc::E2BIG => {
            Ok(RunResult::SandboxUnavailable(format!(
                "refuse-unconfined: the sandbox could not enforce isolation (errno {errno}); no law evidence is collected"
            )))
        }
        libc::ENOEXEC | libc::EACCES => Ok(RunResult::Unrunnable(format!(
            "the bound suite bytes cannot be executed as a program (errno {errno})"
        ))),
        _ => Err(format!(
            "law runner failed to spawn the suite process: {e}"
        )),
    }
}

/// Echo-validate the suite's stdout against runner-derived values; any
/// violation is runner-authored inconclusive, never an accepting result.
/// Proof/exhaustive methods are downgraded to inconclusive (sampled only)
/// while keeping the claimed method in the evidence record.
fn validate_result(text: &str, expected: &ExpectedEcho) -> Result<RunResult, String> {
    let reason = |why: String| Ok(RunResult::Inconclusive(format!("runner: {why}")));
    let value = match formats::parse(text) {
        Ok(v) => v,
        Err(e) => return reason(format!("malformed law_result stdout: {e}")),
    };
    let entries = match value.as_obj() {
        Some(entries) => entries,
        None => return reason("law_result stdout is not a JSON object".to_string()),
    };
    for (key, _) in entries {
        if !LAW_RESULT_FIELDS.contains(&key.as_str()) {
            return reason(format!("unknown law_result field `{key}`"));
        }
    }
    if let Err(e) = value.str_field("version") {
        return reason(format!("missing law_result field: {e}"));
    }
    if value.str_field("version").unwrap() != "1" {
        return reason(format!(
            "unsupported law_result version `{}`; expected `1`",
            value.str_field("version").unwrap()
        ));
    }
    if value.str_field("kind").unwrap_or_default() != "law_result" {
        return reason("law_result kind mismatch".to_string());
    }
    for (field, want) in [
        ("law_suite", &expected.suite_digest),
        ("contract", &expected.contract_digest),
        ("implementation_artifact", &expected.artifact_digest),
        ("harness", &expected.harness_digest),
    ] {
        let got = value.str_field(field).unwrap_or_default();
        if got != *want {
            return reason(format!(
                "law_result `{field}` echo mismatch: suite emitted `{got}` but the runner derived `{want}`"
            ));
        }
    }
    let got_fixtures: Vec<String> = match value.get("fixtures").and_then(Value::as_arr) {
        Some(items) => {
            let mut out = Vec::new();
            for item in items {
                match item.as_str() {
                    Some(d) => out.push(d.to_string()),
                    None => return reason("law_result fixtures must be digest strings".to_string()),
                }
            }
            out
        }
        None => return reason("law_result fixtures must be an array".to_string()),
    };
    if got_fixtures != expected.fixture_digests {
        return reason("law_result fixture digests do not match the runner's ordered fixture list".to_string());
    }
    match value.get("seed").and_then(Value::as_int) {
        Some(seed) if seed == expected.seed => {}
        _ => return reason("law_result seed does not match the supplied seed".to_string()),
    }
    match value.get("budgets") {
        Some(Value::Obj(entries)) => {
            let ok = entries.len() == 1
                && entries[0].0 == "wall_ms"
                && entries[0].1.as_int() == Some(expected.wall_ms);
            if !ok {
                return reason("law_result budgets do not match the supplied budgets".to_string());
            }
        }
        _ => return reason("law_result budgets must be an object".to_string()),
    }
    let method = value.str_field("method").unwrap_or_default();
    if !matches!(method, "proof" | "exhaustive" | "sampled") {
        return reason(format!("unknown law_result method `{method}`"));
    }
    let status = value.str_field("status").unwrap_or_default();
    if !matches!(status, "pass" | "counterexample" | "inconclusive") {
        return reason(format!("unknown law_result status `{status}`"));
    }
    let witness = value.get("witness");
    let reason_field = value.get("reason");
    if let Some(w) = witness {
        if !matches!(w, Value::Null) && !matches!(w, Value::Str(d) if formats::is_digest(d)) {
            return reason("law_result witness must be null or a digest".to_string());
        }
    }
    if status == "counterexample" && !matches!(witness, Some(Value::Str(_))) {
        return reason("a counterexample requires a witness digest naming the failing input".to_string());
    }
    if status == "inconclusive" {
        if !matches!(reason_field, Some(Value::Str(r)) if !r.is_empty()) {
            return reason("an inconclusive result requires a non-empty diagnostic reason".to_string());
        }
        if !matches!(witness, Some(Value::Null) | None) {
            return reason("an inconclusive result must not claim a witness".to_string());
        }
    } else if !matches!(reason_field, Some(Value::Null) | None) {
        return reason("only inconclusive results carry a diagnostic reason".to_string());
    }
    // D10: proof and exhaustive methods are downgraded — this slice's
    // runner accepts sampled evidence only, regardless of what the suite
    // claims (an emitted proof/exhaustive is downgraded to inconclusive;
    // only sampled yields genuine pass/counterexample). The claimed method
    // is kept in the evidence record.
    let (status, reason, witness) = if method != "sampled" {
        (
            "inconclusive".to_string(),
            Some(format!(
                "runner: {method} method downgraded to inconclusive; sampled evidence is the only accepted method in this slice"
            )),
            None,
        )
    } else {
        (
            status.to_string(),
            match reason_field {
                Some(Value::Str(r)) => Some(r.clone()),
                _ => None,
            },
            match witness {
                Some(Value::Str(w)) => Some(w.clone()),
                _ => None,
            },
        )
    };
    Ok(RunResult::Valid(ParsedResult {
        canonical: formats::canonical(&value),
        method: Some(method.to_string()),
        status,
        witness,
        reason,
    }))
}

/// Apply the resource budgets inside the child, before exec.
unsafe fn apply_rlimits(wall_ms: i64) -> std::io::Result<()> {
    let set = |resource: libc::__rlimit_resource_t, cur: libc::rlim_t| -> std::io::Result<()> {
        let limit = libc::rlimit {
            rlim_cur: cur,
            rlim_max: cur,
        };
        if libc::setrlimit(resource, &limit) != 0 {
            return Err(std::io::Error::last_os_error());
        }
        Ok(())
    };
    set(libc::RLIMIT_FSIZE as libc::__rlimit_resource_t, 0)?;
    set(libc::RLIMIT_NOFILE as libc::__rlimit_resource_t, 64)?;
    set(libc::RLIMIT_NPROC as libc::__rlimit_resource_t, 128)?;
    set(libc::RLIMIT_AS as libc::__rlimit_resource_t, LAW_MEM_LIMIT)?;
    set(
        libc::RLIMIT_CPU as libc::__rlimit_resource_t,
        (wall_ms / 1000).max(10) as libc::rlim_t,
    )?;
    Ok(())
}

/// Confine the child with Landlock before exec: network and all writes
/// denied, reads (and exec) allowed only under the supplied roots plus the
/// system runtime (/usr). Raw syscalls keep the hook async-signal-safe;
/// setup failure reports its errno to the parent as a spawn error.
unsafe fn apply_landlock(roots: &[CString]) -> std::io::Result<()> {
    let abi = landlock_abi_query();
    if abi < 1 {
        return Err(std::io::Error::from_raw_os_error(libc::ENOSYS));
    }
    // Handled access rights: every filesystem right the probed ABI knows,
    // so unlisted paths get nothing; network rights from ABI v4 on.
    let mut fs_bits: u64 = 0x1FFF;
    if abi >= 2 {
        fs_bits |= 1 << 13; // REFER
    }
    if abi >= 3 {
        fs_bits |= 1 << 14; // TRUNCATE
    }
    if abi >= 5 {
        fs_bits |= 1 << 15; // IOCTL_DEV
    }
    let net_bits: u64 = if abi >= 4 { 0b11 } else { 0 }; // BIND_TCP | CONNECT_TCP
    if libc::prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 {
        return Err(std::io::Error::last_os_error());
    }
    #[repr(C)]
    struct RulesetAttr {
        handled_access_fs: u64,
        handled_access_net: u64,
    }
    let attr = RulesetAttr {
        handled_access_fs: fs_bits,
        handled_access_net: net_bits,
    };
    let ruleset_fd = libc::syscall(
        SYS_LANDLOCK_CREATE_RULESET,
        &attr as *const RulesetAttr,
        std::mem::size_of::<RulesetAttr>() as libc::c_uint,
        0 as libc::c_uint,
    );
    if ruleset_fd < 0 {
        return Err(std::io::Error::last_os_error());
    }
    #[repr(C)]
    struct PathBeneathAttr {
        allowed_access: u64,
        parent_fd: u64,
    }
    for root in roots {
        let path_fd = libc::openat(libc::AT_FDCWD, root.as_ptr(), O_PATH | libc::O_CLOEXEC);
        if path_fd < 0 {
            libc::close(ruleset_fd as libc::c_int);
            return Err(std::io::Error::last_os_error());
        }
        let rule = PathBeneathAttr {
            allowed_access: LANDLOCK_ACCESS_FS_READ_FILE
                | LANDLOCK_ACCESS_FS_READ_DIR
                | LANDLOCK_ACCESS_FS_EXECUTE,
            parent_fd: path_fd as u64,
        };
        let added = libc::syscall(
            SYS_LANDLOCK_ADD_RULE,
            ruleset_fd as libc::c_int,
            LANDLOCK_RULE_PATH_BENEATH,
            &rule as *const PathBeneathAttr,
            0 as libc::c_uint,
        );
        libc::close(path_fd);
        if added < 0 {
            libc::close(ruleset_fd as libc::c_int);
            return Err(std::io::Error::last_os_error());
        }
    }
    if libc::syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd as libc::c_int, 0 as libc::c_uint) < 0 {
        libc::close(ruleset_fd as libc::c_int);
        return Err(std::io::Error::last_os_error());
    }
    libc::close(ruleset_fd as libc::c_int);
    Ok(())
}
