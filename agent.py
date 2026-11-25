"""
PKTron Agent — Pakistan's first AI-powered quantum circuit agent.

Pipeline: BRAIN (writes code) -> HANDS (runs PKTron) -> EYES (validates)
          -> self-fix loop (max 3 tries) -> MOUTH (plain-language explanation)

Requires: pip install pktron google-generativeai
Set your Google API key in the GOOGLE_API_KEY environment variable.
"""

import os
import re
import json
import traceback
import numpy as np
import pktron
import google.generativeai as genai

MODEL = "models/gemini-2.5-flash"  # swap to gemini-1.5-pro if you have access
MAX_FIX_ATTEMPTS = 3

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# ---------------------------------------------------------------------------
# 1. THE MENU — known circuit types the agent is allowed to build (v1 scope)
#    Keeping this fixed and small is what makes the agent reliable.
#    Add more entries here later once the core loop is proven.
# ---------------------------------------------------------------------------
CIRCUIT_MENU = {
    "superposition": "A single qubit in equal superposition (Hadamard gate).",
    "bell_state": "Two qubits maximally entangled (Bell/EPR pair).",
    "ghz_state": "Three (or more) qubits maximally entangled together (GHZ state).",
    "deutsch_jozsa": "Deutsch-Jozsa algorithm distinguishing constant vs balanced functions.",
    "grover_2qubit": "Grover's search algorithm on a 2-qubit space (finds a marked item).",
    "teleportation": "Quantum teleportation protocol moving a qubit's state via entanglement.",
    "qft": "Quantum Fourier Transform on a small number of qubits.",
    "entanglement_swap": "Entanglement swapping between two separate Bell pairs.",
}

BRAIN_SYSTEM_PROMPT = f"""You are the "Brain" of the PKTron Agent, a quantum-circuit-writing
assistant built on the PKTron simulator (a real installed Python package, version 13).

Your job: given a plain-English request, choose the closest matching circuit type from
this fixed menu, then write PYTHON CODE that builds and runs it using PKTron's real API.

AVAILABLE CIRCUIT TYPES (pick the closest match, don't invent new ones in v1):
{json.dumps(CIRCUIT_MENU, indent=2)}

VERIFIED REAL PKTRON API (use ONLY this — do not invent methods):
- pktron.QuantumCircuit(n_qubits)              # create a circuit
- qc.h(qubit_index)                            # Hadamard
- qc.x(qubit_index), qc.y(...), qc.z(...)      # Pauli gates
- qc.cx(control, target)                       # CNOT
- qc.cz(control, target)                       # controlled-Z
- qc.ccx(c1, c2, target)                       # Toffoli
- qc.swap(q1, q2)
- qc.rx(theta, qubit), qc.ry(theta, qubit), qc.rz(theta, qubit)
- qc.measure(qubit_list, clbit_list)           # optional; counts are returned even without this
- qc.save_statevector()                        # call this before execute() to get the statevector
- pktron.execute(qc, backend=pktron.StatevectorSimulator(), shots=1024)
    -> returns a dict with keys: 'counts' (dict of bitstring->count),
       'statevector' (complex numpy array), 'snapshots'

RULES:
1. Output ONLY a JSON object, nothing else, no markdown fences, no commentary.
2. JSON shape:
   {{
     "circuit_type": "<one of the menu keys>",
     "code": "<python code as a single string, using the variable name 'qc' for the circuit
               and 'result' for the pktron.execute(...) return value>",
     "intent_description": "<one sentence, plain English, what this circuit should produce>"
   }}
3. The code must assign the circuit to `qc`, call qc.save_statevector() before execute(),
   and assign the execute() output to `result`. Do not call print(). Do not import anything
   (pktron and numpy as np are already available).
4. If you are fixing a previous error, read the error message carefully and correct the
   exact mistake — do not rewrite unrelated parts of the circuit.
"""

MOUTH_SYSTEM_PROMPT = """You are the "Mouth" of the PKTron Agent. You explain quantum
circuit results to a non-technical reader in simple, friendly, layman language.
No jargon without explaining it. Keep it to 3-5 short sentences. Mention what the
numbers/statevector actually mean in plain terms (e.g. "this means the two qubits
are now linked: measuring one instantly tells you the other's value")."""


def _call_brain(user_request: str, previous_error: str = None, previous_code: str = None) -> dict:
    """Ask the LLM to write (or fix) PKTron code for the request."""
    if previous_error:
        user_msg = (
            f"Original request: {user_request}\n\n"
            f"Your previous code:\n{previous_code}\n\n"
            f"That code produced this error when run:\n{previous_error}\n\n"
            f"Fix it. Return the corrected JSON object only."
        )
    else:
        user_msg = f"Request: {user_request}"

    model = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=BRAIN_SYSTEM_PROMPT,
    )
    response = model.generate_content(user_msg)
    text = response.text.strip()
    # strip accidental markdown fences just in case
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    return json.loads(text)


def _run_pktron_code(code: str):
    """Execute the Brain's generated code in a restricted namespace."""
    namespace = {"pktron": pktron, "np": np}
    exec(code, namespace)
    return namespace.get("qc"), namespace.get("result")


# ---------------------------------------------------------------------------
# 2. EYES — simple, fast correctness checks per circuit type.
#    These don't need formal proofs; for small known circuits, checking the
#    statevector/counts against the expected pattern is enough.
# ---------------------------------------------------------------------------
def _validate(circuit_type: str, qc, result) -> tuple:
    """Returns (is_valid: bool, reason: str)."""
    sv = result.get("statevector")
    counts = result.get("counts", {})

    if circuit_type == "superposition":
        if sv is None or len(sv) < 2:
            return False, "No valid statevector returned."
        probs = np.abs(sv) ** 2
        if abs(probs[0] - 0.5) < 0.05 and abs(probs[1] - 0.5) < 0.05:
            return True, "Equal 50/50 superposition confirmed."
        return False, f"Expected ~50/50 probabilities, got {probs[:2]}"

    if circuit_type == "bell_state":
        if len(counts) == 2 and set(counts.keys()) <= {"00", "11"}:
            return True, "Only '00' and '11' outcomes seen — correct Bell correlation."
        return False, f"Expected only '00'/'11' outcomes, got {counts}"

    if circuit_type == "ghz_state":
        if set(counts.keys()) <= {"000", "111"} and len(counts) > 0:
            return True, "Only all-zeros/all-ones outcomes seen — correct GHZ correlation."
        return False, f"Expected only '000'/'111' outcomes, got {counts}"

    # Generic fallback for menu items without a specific check yet (v1):
    if sv is not None:
        norm = np.sum(np.abs(sv) ** 2)
        if abs(norm - 1.0) < 1e-3:
            return True, "Statevector is normalized (valid quantum state)."
        return False, f"Statevector not normalized (sum of |amp|^2 = {norm})."

    return True, "No statevector-based check available for this circuit type; ran without error."


# ---------------------------------------------------------------------------
# 3. MOUTH — plain-language explanation
# ---------------------------------------------------------------------------
def _explain(user_request: str, circuit_type: str, result: dict, is_valid: bool, reason: str) -> str:
    counts = result.get("counts", {})
    model = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=MOUTH_SYSTEM_PROMPT,
    )
    response = model.generate_content(
        f"User asked for: {user_request}\n"
        f"Circuit type built: {circuit_type}\n"
        f"Measurement counts: {counts}\n"
        f"Validation result: {'PASSED' if is_valid else 'FAILED'} — {reason}\n"
        f"Explain this result in plain language."
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------
def run_pktron_agent(user_request: str) -> dict:
    """
    Full agent loop: plan -> act -> observe -> fix -> explain.
    Returns a dict with everything the front end needs to display.
    """
    previous_error = None
    previous_code = None
    last_brain_output = None

    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        try:
            brain_output = _call_brain(user_request, previous_error, previous_code)
            last_brain_output = brain_output
            code = brain_output["code"]

            qc, result = _run_pktron_code(code)
            if result is None:
                raise RuntimeError("Code ran but did not produce a `result` variable.")

            is_valid, reason = _validate(brain_output["circuit_type"], qc, result)

            if is_valid:
                explanation = _explain(user_request, brain_output["circuit_type"], result, True, reason)
                return {
                    "success": True,
                    "attempts": attempt,
                    "circuit_type": brain_output["circuit_type"],
                    "code": code,
                    "counts": result.get("counts"),
                    "statevector": [str(x) for x in result.get("statevector")] if result.get("statevector") is not None else None,
                    "validation_reason": reason,
                    "explanation": explanation,
                }
            else:
                previous_error = f"Validation failed: {reason}"
                previous_code = code
                continue

        except Exception as e:
            previous_error = f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=2)}"
            previous_code = last_brain_output.get("code") if last_brain_output else "N/A"
            continue

    return {
        "success": False,
        "attempts": MAX_FIX_ATTEMPTS,
        "last_error": previous_error,
        "last_code": previous_code,
        "message": "The agent could not produce a valid circuit after multiple attempts. "
                   "See last_error and last_code for debugging.",
    }


if __name__ == "__main__":
    # quick manual test from the command line
    import sys
    request = " ".join(sys.argv[1:]) or "make a bell state"
    output = run_pktron_agent(request)
    print(json.dumps(output, indent=2, default=str))
