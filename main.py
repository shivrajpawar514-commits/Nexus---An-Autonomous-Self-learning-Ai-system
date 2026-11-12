"""Autonomous Self-Learning AI Agent System - CLI Entry Point."""

import argparse
import sys
from agent.llm import MockLLM
from agent.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Self-Learning AI Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute an autonomous task")
    run_parser.add_argument("goal", type=str, help="High-level goal for the agent")
    run_parser.add_argument("--no-memory", action="store_true", help="Disable memory retrieval")
    run_parser.add_argument("--no-reflect", action="store_true", help="Disable reflection learning")
    run_parser.add_argument("--provider", type=str, default="mock", choices=["mock", "ollama", "openai"], help="LLM Provider")
    run_parser.add_argument("--workflow", action="store_true", help="Execute via LangGraph StateGraph workflow")

    # Command: eval
    eval_parser = subparsers.add_parser("eval", help="Run benchmark evaluation")
    eval_parser.add_argument("--split", type=str, default="test", choices=["train", "val", "test"])

    # Command: learn
    learn_parser = subparsers.add_parser("learn", help="Run multi-iteration self-learning experiment")
    learn_parser.add_argument("--cycles", type=int, default=3, help="Number of learning cycles")

    # Command: stats
    subparsers.add_parser("stats", help="Inspect episodic memory and system telemetry")

    # Command: dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Launch interactive mission control web dashboard")
    dash_parser.add_argument("--port", type=int, default=8080, help="Port to bind dashboard server (default: 8080)")
    dash_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")

    args = parser.parse_args()

    if not args.command or args.command == "run":
        goal = getattr(args, "goal", "Calculate the sum of all prime numbers between 1 and 20.")
        use_mem = not getattr(args, "no_memory", False)
        use_ref = not getattr(args, "no_reflect", False)

        print("\n" + "=" * 60)
        print("  AUTONOMOUS SELF-LEARNING AGENT SYSTEM")
        print("=" * 60)
        print(f"Goal: {goal}")
        print(f"Memory: {'Enabled' if use_mem else 'Disabled'} | Reflection: {'Enabled' if use_ref else 'Disabled'}\n")

        from agent.llm import get_llm
        provider = getattr(args, "provider", "mock")
        use_workflow = getattr(args, "workflow", False)
        llm = get_llm(provider)

        if use_workflow:
            from graph.workflow import AgentWorkflow
            wf = AgentWorkflow(llm=llm)
            state = wf.run(goal, use_memory=use_mem, use_reflection=use_ref)
            print("\n--- LangGraph Workflow Trajectory ---")
            if state.execution:
                for s in state.execution.trajectory:
                    print(f"Step {s.step_index}:")
                    print(f"  Thought: {s.thought}")
                    if s.action_name:
                        print(f"  Action:  {s.action_name}({s.action_args})")
                    if s.observation:
                        print(f"  Obs:     {s.observation[:120]}...")
            print("\n--- Final Verdict ---")
            print(f"Passed:   {state.verdict.passed if state.verdict else False}")
            print(f"Status:   {state.status}")
            if state.execution:
                print(f"Answer:   {state.execution.answer}")
                print(f"Total Steps: {state.execution.total_steps} | Tokens: {state.execution.total_tokens}")
            if state.reflection and state.reflection.lessons:
                print("\n--- Extracted Reflection & Lessons ---")
                for l in state.reflection.lessons:
                    print(f"Rule:       {l.rule}")
        else:
            orchestrator = Orchestrator(llm=llm)
            report = orchestrator.run_task(goal, use_memory=use_mem, use_reflection=use_ref)

            print("\n--- Execution Trajectory ---")
            for s in report.execution.trajectory:
                print(f"Step {s.step_index}:")
                print(f"  Thought: {s.thought}")
                if s.action_name:
                    print(f"  Action:  {s.action_name}({s.action_args})")
                if s.observation:
                    print(f"  Obs:     {s.observation[:120]}...")

            print("\n--- Final Verdict ---")
            print(f"Passed:   {report.passed}")
            print(f"Score:    {report.verdict.score}")
            print(f"Evidence: {report.verdict.evidence}")
            print(f"Total Steps: {report.execution.total_steps} | Tokens: {report.execution.total_tokens}")

            if report.reflection and report.reflection.lessons:
                print("\n--- Extracted Reflection & Lessons ---")
                for l in report.reflection.lessons:
                    print(f"Rule:       {l.rule}")
                    print(f"Root Cause: {l.root_cause}")
                    print(f"Confidence: {l.confidence} (Trust Weight: {l.trust_weight})")

    elif args.command == "eval":
        from eval.run import evaluate_split
        llm = MockLLM()
        orchestrator = Orchestrator(llm=llm)
        evaluate_split(orchestrator, split=args.split)

    elif args.command == "learn":
        from eval.run import run_learning_cycle
        run_learning_cycle(num_iterations=args.cycles)

    elif args.command == "stats":
        llm = MockLLM()
        orchestrator = Orchestrator(llm=llm)
        stats = orchestrator.episodic_memory.get_summary_stats()
        print("\n--- Episodic Memory Telemetry ---")
        for k, v in stats.items():
            print(f"{k.replace('_', ' ').title():<20}: {v}")

    elif args.command == "dashboard":
        from dashboard.server import run_dashboard
        run_dashboard(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

