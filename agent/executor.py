"""ReAct Executor implementing Thought -> Action -> Observation loop with validation & budget enforcement."""

from __future__ import annotations
import ast
import json
import re
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent.llm import LLMInterface
from tools.base import ToolRegistry, ToolResult, get_default_registry


class ReActStep(BaseModel):
    step_index: int
    thought: str
    action_name: Optional[str] = None
    action_args: Dict[str, Any] = Field(default_factory=dict)
    observation: Optional[str] = None
    duration_sec: float = 0.0
    tokens_used: int = 0


class ExecutionResult(BaseModel):
    ok: bool
    answer: str
    trajectory: List[ReActStep] = Field(default_factory=list)
    total_steps: int = 0
    total_tokens: int = 0
    duration_sec: float = 0.0
    error: Optional[str] = None


class Executor:
    def __init__(
        self,
        llm: LLMInterface,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: int = 10,
        token_budget: int = 50000,
        timeout_seconds: float = 60.0,
    ):
        self.llm = llm
        self.tool_registry = tool_registry or get_default_registry()
        self.max_steps = max_steps
        self.token_budget = token_budget
        self.timeout_seconds = timeout_seconds

    def _parse_action_call(self, text: str) -> tuple[str, Optional[str], Dict[str, Any]]:
        """Parses Thought and Action: tool_name(arg1=val1, ...) or finish(answer=...)."""
        thought = ""
        action_name = None
        action_args: Dict[str, Any] = {}

        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
        else:
            thought = text.strip()

        # Extract Action
        m = re.search(r"Action:\s*([a-zA-Z_0-9]+)\(", text, re.IGNORECASE)
        if m:
            action_name = m.group(1).strip()
            start_idx = m.end() - 1
            depth = 0
            end_idx = -1
            in_single = False
            in_double = False
            for i in range(start_idx, len(text)):
                ch = text[i]
                if ch == "'" and not in_double:
                    in_single = not in_single
                elif ch == '"' and not in_single:
                    in_double = not in_double
                elif not in_single and not in_double:
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            end_idx = i
                            break
            if end_idx != -1:
                args_str = text[start_idx + 1 : end_idx].strip()
            else:
                args_str = text[start_idx + 1 :].rstrip(")").strip()

            if args_str:
                # 1. Try standard AST keyword parse
                parsed = False
                try:
                    fake_call = f"dummy({args_str})"
                    tree = ast.parse(fake_call)
                    for kw in tree.body[0].value.keywords:
                        val = ast.literal_eval(kw.value)
                        action_args[kw.arg] = val
                    parsed = True
                except Exception:
                    pass

                # 2. Try single kwarg regex parse for multiline strings
                if not parsed:
                    kw_m = re.match(r"^([a-zA-Z_0-9]+)\s*=\s*['\"](.*)['\"]$", args_str, re.DOTALL)
                    if kw_m:
                        action_args[kw_m.group(1)] = kw_m.group(2)
                        parsed = True

                # 3. Fallback JSON / raw string handling
                if not parsed:
                    try:
                        action_args = json.loads(f"{{{args_str}}}")
                    except Exception:
                        action_args = {"raw_input": args_str}
        else:
            # Check for simple finish or finish: text
            if "finish" in text.lower():
                action_name = "finish"
                action_args = {"answer": text}

        return thought, action_name, action_args

    def run(
        self,
        goal: str,
        context: Optional[str] = None,
        retrieved_lessons: Optional[List[str]] = None,
        retrieved_skills: Optional[List[str]] = None,
    ) -> ExecutionResult:
        start_time = time.time()
        trajectory: List[ReActStep] = []
        accumulated_tokens = 0

        # Build tools description
        tools_docs = []
        for t in self.tool_registry.list_tools():
            tools_docs.append(f"- {t.name}: {t.description} | Params: {t.parameters_schema.get('properties', {})}")
        tools_docs.append("- finish(answer=str): Finalizes the task with the final answer.")
        tools_prompt = "\n".join(tools_docs)

        lessons_text = ""
        if retrieved_lessons:
            lessons_text = "\n### Learned Lessons from Previous Runs (DO NOT REPEAT PAST MISTAKES):\n" + "\n".join(
                f"- {l}" for l in retrieved_lessons
            )

        skills_text = ""
        if retrieved_skills:
            skills_text = "\n### Reusable Skills Available in Library:\n" + "\n".join(
                f"- {s}" for s in retrieved_skills
            )

        system_prompt = (
            "You are an autonomous AI problem-solving agent running a ReAct loop.\n"
            "Format your response strictly as:\n"
            "Thought: <your step-by-step reasoning>\n"
            "Action: <tool_name>(<kwargs>)\n\n"
            f"Available Tools:\n{tools_prompt}\n"
            f"{lessons_text}\n"
            f"{skills_text}\n"
        )

        history_dialogue = f"Goal: {goal}\n"
        if context:
            history_dialogue += f"Prior Context: {context}\n"

        for step_idx in range(1, self.max_steps + 1):
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                return ExecutionResult(
                    ok=False,
                    answer="",
                    trajectory=trajectory,
                    total_steps=step_idx,
                    total_tokens=accumulated_tokens,
                    duration_sec=elapsed,
                    error=f"Task exceeded timeout limit ({self.timeout_seconds}s).",
                )

            if accumulated_tokens > self.token_budget:
                return ExecutionResult(
                    ok=False,
                    answer="",
                    trajectory=trajectory,
                    total_steps=step_idx,
                    total_tokens=accumulated_tokens,
                    duration_sec=elapsed,
                    error=f"Task exceeded token budget ({self.token_budget} tokens).",
                )

            # Call LLM
            step_start = time.time()
            prompt = (
                f"{history_dialogue}\n"
                f"Begin Step {step_idx} (Output Thought and Action):"
            )
            response = self.llm.generate(prompt, system_prompt=system_prompt)
            accumulated_tokens += response.total_tokens

            thought, action_name, action_args = self._parse_action_call(response.content)

            step = ReActStep(
                step_index=step_idx,
                thought=thought,
                action_name=action_name,
                action_args=action_args,
                tokens_used=response.total_tokens,
            )

            # Check if finished
            if action_name == "finish" or not action_name:
                ans = action_args.get("answer", thought)
                step.observation = "Task completed."
                step.duration_sec = time.time() - step_start
                trajectory.append(step)
                return ExecutionResult(
                    ok=True,
                    answer=ans,
                    trajectory=trajectory,
                    total_steps=step_idx,
                    total_tokens=accumulated_tokens,
                    duration_sec=time.time() - start_time,
                )

            # Execute tool
            tool_res: ToolResult = self.tool_registry.execute(action_name, **action_args)
            obs_str = tool_res.to_observation_str()
            step.observation = obs_str
            step.duration_sec = time.time() - step_start
            trajectory.append(step)

            # Append to history dialogue
            history_dialogue += (
                f"\nStep {step_idx}:\n"
                f"Thought: {thought}\n"
                f"Action: {action_name}({action_args})\n"
                f"Observation: {obs_str}\n"
            )

        return ExecutionResult(
            ok=False,
            answer="",
            trajectory=trajectory,
            total_steps=self.max_steps,
            total_tokens=accumulated_tokens,
            duration_sec=time.time() - start_time,
            error=f"Reached maximum step limit ({self.max_steps}) without finishing.",
        )

