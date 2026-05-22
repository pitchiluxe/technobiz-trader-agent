"""
Workflow Orchestrator with Strict Phase Enforcement

Ensures the trading workflow strictly follows:
  PHASE 1: Trend-Master (Market Analysis)
  PHASE 2: Analyse-Master (Entry Signal Generation)
  PHASE 3: Trader-Master (Trade Execution)

No phase can be skipped, and each must complete before the next begins.
"""

import logging
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Trading workflow phases."""

    INITIALIZATION = "INITIALIZATION"
    TREND_ANALYSIS = "TREND_ANALYSIS"
    SIGNAL_GENERATION = "SIGNAL_GENERATION"
    TRADE_EXECUTION = "TRADE_EXECUTION"
    COMPLETE = "COMPLETE"


class WorkflowState:
    """Represents the state of a single trading workflow execution."""

    def __init__(self, symbol: str, cycle_id: Optional[str] = None):
        """
        Initialize workflow state.

        Args:
            symbol: Trading pair being analyzed
            cycle_id: Unique identifier for this cycle (auto-generated if not provided)
        """
        self.cycle_id = cycle_id or str(uuid.uuid4())[:8]
        self.symbol = symbol
        self.phase = WorkflowPhase.INITIALIZATION
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None

        # Phase outputs
        self.trend_report: Optional[Dict[str, Any]] = None
        self.trade_signal: Optional[Dict[str, Any]] = None
        self.execution_record: Optional[Dict[str, Any]] = None

        # Errors
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def transition_to(self, next_phase: WorkflowPhase) -> bool:
        """
        Transition to the next phase with validation.

        Args:
            next_phase: The phase to transition to

        Returns:
            True if transition was successful, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            WorkflowPhase.INITIALIZATION: [WorkflowPhase.TREND_ANALYSIS],
            WorkflowPhase.TREND_ANALYSIS: [WorkflowPhase.SIGNAL_GENERATION],
            WorkflowPhase.SIGNAL_GENERATION: [WorkflowPhase.TRADE_EXECUTION],
            WorkflowPhase.TRADE_EXECUTION: [WorkflowPhase.COMPLETE],
        }

        current = self.phase
        allowed_next = valid_transitions.get(current, [])

        if next_phase not in allowed_next:
            error_msg = (
                f"Invalid phase transition: {current.value} → {next_phase.value}. "
                f"Allowed: {[p.value for p in allowed_next]}"
            )
            logger.error(f"[WORKFLOW {self.cycle_id}] {error_msg}")
            self.errors.append(error_msg)
            return False

        logger.info(
            f"[WORKFLOW {self.cycle_id}] Phase transition: "
            f"{current.value} → {next_phase.value}"
        )
        self.phase = next_phase
        return True

    def set_trend_report(self, report: Dict[str, Any]) -> bool:
        """Set trend report (phase: TREND_ANALYSIS)."""
        if self.phase != WorkflowPhase.TREND_ANALYSIS:
            error = f"Cannot set trend report outside TREND_ANALYSIS phase (current: {self.phase.value})"
            logger.error(f"[WORKFLOW {self.cycle_id}] {error}")
            self.errors.append(error)
            return False

        if not report or not report.get('bias'):
            error = "Invalid trend report: missing required fields"
            logger.error(f"[WORKFLOW {self.cycle_id}] {error}")
            self.errors.append(error)
            return False

        self.trend_report = report
        logger.info(
            f"[WORKFLOW {self.cycle_id}] Trend Report set: "
            f"bias={report.get('bias')}, confidence={report.get('confidence')}%"
        )
        return True

    def set_trade_signal(self, signal: Dict[str, Any]) -> bool:
        """Set trade signal (phase: SIGNAL_GENERATION)."""
        if self.phase != WorkflowPhase.SIGNAL_GENERATION:
            error = f"Cannot set trade signal outside SIGNAL_GENERATION phase (current: {self.phase.value})"
            logger.error(f"[WORKFLOW {self.cycle_id}] {error}")
            self.errors.append(error)
            return False

        if not signal or not signal.get('direction'):
            error = "Invalid trade signal: missing required fields"
            logger.error(f"[WORKFLOW {self.cycle_id}] {error}")
            self.errors.append(error)
            return False

        self.trade_signal = signal
        logger.info(
            f"[WORKFLOW {self.cycle_id}] Trade Signal set: "
            f"direction={signal.get('direction')}, entry={signal.get('entry_level')}"
        )
        return True

    def set_execution_record(self, record: Dict[str, Any]) -> bool:
        """Set execution record (phase: TRADE_EXECUTION)."""
        if self.phase != WorkflowPhase.TRADE_EXECUTION:
            error = f"Cannot set execution record outside TRADE_EXECUTION phase (current: {self.phase.value})"
            logger.error(f"[WORKFLOW {self.cycle_id}] {error}")
            self.errors.append(error)
            return False

        if not record or not record.get('status'):
            error = "Invalid execution record: missing required fields"
            logger.error(f"[WORKFLOW {self.cycle_id}] {error}")
            self.errors.append(error)
            return False

        self.execution_record = record
        logger.info(
            f"[WORKFLOW {self.cycle_id}] Execution Record set: "
            f"status={record.get('status')}, ticket={record.get('mt5_ticket')}"
        )
        return True

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.phase == WorkflowPhase.COMPLETE

    def finalize(self) -> None:
        """Finalize the workflow."""
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"[WORKFLOW {self.cycle_id}] Workflow completed in {duration:.2f}s")

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary."""
        duration = (
            (self.end_time - self.start_time).total_seconds()
            if self.end_time
            else None
        )

        return {
            'cycle_id': self.cycle_id,
            'symbol': self.symbol,
            'phase': self.phase.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'trend_report': bool(self.trend_report),
            'trade_signal': bool(self.trade_signal),
            'execution_record': bool(self.execution_record),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }


class WorkflowOrchestrator:
    """
    Orchestrates the three-phase trading workflow with strict phase enforcement.

    Ensures:
    1. Each phase completes before the next begins
    2. No phase is skipped
    3. Valid data flows between phases
    4. Workflow can be audited and traced
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.current_workflow: Optional[WorkflowState] = None
        self.completed_workflows: list[WorkflowState] = []
        self.max_phase_duration = timedelta(seconds=300)  # 5 minutes max per phase

        logger.info("[ORCHESTRATOR] Trading Workflow Orchestrator initialized")

    def start_cycle(self, symbol: str) -> WorkflowState:
        """
        Start a new trading cycle for a symbol.

        Args:
            symbol: Trading pair to analyze

        Returns:
            New WorkflowState instance
        """
        logger.info(f"\n{'═' * 70}")
        logger.info(f"[ORCHESTRATOR] STARTING NEW TRADING CYCLE")
        logger.info(f"{'═' * 70}")

        if self.current_workflow and not self.current_workflow.is_complete():
            warning = (
                f"Previous workflow still in progress (phase: "
                f"{self.current_workflow.phase.value})"
            )
            logger.warning(f"[ORCHESTRATOR] {warning}")
            self.current_workflow.warnings.append(warning)

        self.current_workflow = WorkflowState(symbol)
        logger.info(
            f"[ORCHESTRATOR] Cycle ID: {self.current_workflow.cycle_id} | "
            f"Symbol: {symbol}"
        )
        return self.current_workflow

    def begin_trend_analysis(self) -> bool:
        """
        Begin PHASE 1: Trend Analysis.

        Returns:
            True if phase started successfully
        """
        if not self.current_workflow:
            logger.error("[ORCHESTRATOR] No active workflow")
            return False

        if not self.current_workflow.transition_to(WorkflowPhase.TREND_ANALYSIS):
            return False

        logger.info(
            f"[ORCHESTRATOR] ┌─ PHASE 1: TREND-MASTER ANALYSIS"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Analyzing market structure across"
            f" timeframes (Daily/4H/1H)"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Expected output: TrendReport with bias"
            f" & support/resistance"
        )

        return True

    def complete_trend_analysis(self, report: Dict[str, Any]) -> bool:
        """
        Complete PHASE 1 and store trend report.

        Args:
            report: TrendReport from Trend-Master

        Returns:
            True if trend report was successfully stored
        """
        if not self.current_workflow:
            logger.error("[ORCHESTRATOR] No active workflow")
            return False

        if not self.current_workflow.set_trend_report(report):
            return False

        logger.info(
            f"[ORCHESTRATOR] └─ PHASE 1 COMPLETE"
        )

        return True

    def begin_signal_generation(self) -> bool:
        """
        Begin PHASE 2: Signal Generation.

        Returns:
            True if phase started successfully
        """
        if not self.current_workflow:
            logger.error("[ORCHESTRATOR] No active workflow")
            return False

        # Verify PHASE 1 output exists
        if not self.current_workflow.trend_report:
            error = "Cannot start signal generation: no trend report from Phase 1"
            logger.error(f"[ORCHESTRATOR] {error}")
            self.current_workflow.errors.append(error)
            return False

        if not self.current_workflow.transition_to(WorkflowPhase.SIGNAL_GENERATION):
            return False

        logger.info(
            f"[ORCHESTRATOR] ┌─ PHASE 2: ANALYSE-MASTER - ICT PATTERN DETECTION"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Input: TrendReport (bias="
            f"{self.current_workflow.trend_report.get('bias')})"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Detecting: Liquidity Sweep, BoS,"
            f" Order Block, Pullback"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Expected output: TradeSignal with all"
            f" 4 ICT elements"
        )

        return True

    def complete_signal_generation(self, signal: Dict[str, Any]) -> bool:
        """
        Complete PHASE 2 and store trade signal.

        Args:
            signal: TradeSignal from Analyse-Master

        Returns:
            True if trade signal was successfully stored
        """
        if not self.current_workflow:
            logger.error("[ORCHESTRATOR] No active workflow")
            return False

        if not self.current_workflow.set_trade_signal(signal):
            return False

        logger.info(
            f"[ORCHESTRATOR] └─ PHASE 2 COMPLETE"
        )

        return True

    def begin_trade_execution(self) -> bool:
        """
        Begin PHASE 3: Trade Execution.

        Returns:
            True if phase started successfully
        """
        if not self.current_workflow:
            logger.error("[ORCHESTRATOR] No active workflow")
            return False

        # Verify PHASE 1 & 2 outputs exist
        if not self.current_workflow.trend_report:
            error = "Cannot start execution: no trend report from Phase 1"
            logger.error(f"[ORCHESTRATOR] {error}")
            self.current_workflow.errors.append(error)
            return False

        if not self.current_workflow.trade_signal:
            error = "Cannot start execution: no trade signal from Phase 2"
            logger.error(f"[ORCHESTRATOR] {error}")
            self.current_workflow.errors.append(error)
            return False

        if not self.current_workflow.transition_to(WorkflowPhase.TRADE_EXECUTION):
            return False

        logger.info(
            f"[ORCHESTRATOR] ┌─ PHASE 3: TRADER-MASTER - TRADE EXECUTION"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Input: TradeSignal (entry="
            f"{self.current_workflow.trade_signal.get('entry_level')})"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Validating: Confidence ≥75%, R:R ≥1:2,"
            f" Risk ≤2%"
        )
        logger.info(
            f"[ORCHESTRATOR] │  Expected output: ExecutionRecord or"
            f" REJECTION"
        )

        return True

    def complete_trade_execution(
        self, record: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Complete PHASE 3 and store execution record or mark rejection.

        Args:
            record: ExecutionRecord from Trader-Master, or None if rejected

        Returns:
            True if execution was processed successfully
        """
        if not self.current_workflow:
            logger.error("[ORCHESTRATOR] No active workflow")
            return False

        if record:
            if not self.current_workflow.set_execution_record(record):
                return False
        else:
            logger.info(
                f"[ORCHESTRATOR] Trade rejected by risk management"
            )

        if not self.current_workflow.transition_to(WorkflowPhase.COMPLETE):
            return False

        logger.info(
            f"[ORCHESTRATOR] └─ PHASE 3 COMPLETE"
        )

        # Finalize workflow
        self.current_workflow.finalize()
        self.completed_workflows.append(self.current_workflow)

        logger.info(f"\n{'═' * 70}")
        logger.info(f"[ORCHESTRATOR] TRADING CYCLE COMPLETE")
        logger.info(f"{'═' * 70}\n")

        return True

    def get_current_workflow(self) -> Optional[WorkflowState]:
        """Get currently active workflow."""
        return self.current_workflow

    def get_workflow_history(self) -> list[Dict[str, Any]]:
        """Get summary of all completed workflows."""
        return [workflow.get_summary() for workflow in self.completed_workflows]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics across all workflows."""
        if not self.completed_workflows:
            return {
                'total_cycles': 0,
                'successful_signals': 0,
                'executed_trades': 0,
                'rejected_trades': 0,
                'average_phase_duration': 0,
            }

        successful = [w for w in self.completed_workflows if w.trade_signal]
        executed = [w for w in self.completed_workflows if w.execution_record]
        rejected = [w for w in self.completed_workflows if not w.execution_record and w.trade_signal]

        total_duration = sum(
            (w.end_time - w.start_time).total_seconds()
            for w in self.completed_workflows
            if w.end_time
        )
        avg_duration = (
            total_duration / len(self.completed_workflows)
            if self.completed_workflows
            else 0
        )

        return {
            'total_cycles': len(self.completed_workflows),
            'successful_signals': len(successful),
            'executed_trades': len(executed),
            'rejected_trades': len(rejected),
            'average_cycle_duration_seconds': avg_duration,
        }
