# Architecture — Class Diagram

This diagram satisfies the §8.6 requirement: "must add an architecture diagram showing class
structure and relationships."

## Class Hierarchy & Relationships

```mermaid
classDiagram
    direction TB

    class BaseAgent {
        <<abstract>>
        +role: AgentRole
        #_config: ConfigManager
        #_gatekeeper: ApiGatekeeper
        #_skill_description: str
        #_client: Anthropic
        #_model: str
        #_load_skill() str
        #_call_llm(system, messages, use_search) tuple
        #_validate_message(msg) None
        +run()* None
    }

    class FatherAgent {
        #_bus: MessageBus | None
        +route(message) None
        +evaluate_debate(transcript) Verdict
        +run() None
    }

    class ProAgent {
        #_bus: MessageBus | None
        #_round_number: int
        #_prev_con_msg: DebateMessage | None
        +generate_argument(round_number, prev_con_msg) DebateMessage
        +run() None
    }

    class ConAgent {
        #_bus: MessageBus | None
        +generate_counter(round_number, pro_msg) DebateMessage
        +run() None
    }

    class DebateOrchestrator {
        #_config: ConfigManager
        #_gatekeeper: ApiGatekeeper
        #_pro: ProAgent
        #_con: ConAgent
        #_father: FatherAgent
        #_procs: dict[str, Process]
        #_watchdog: Watchdog | None
        #_use_processes: bool
        +session_id: str
        +run(topic) tuple[list, Verdict]
        +stop() None
        +get_session_id() str
        +get_transcript() list[DebateMessage]
        +get_verdict() Verdict | None
        #_start_processes() None
        #_start_watchdog() None
        #_run_rounds() None
    }

    class Watchdog {
        #_entries: list[WatchdogEntry]
        #_running: bool
        #_error_event: Event
        #_fatal_error: ProcessUnrecoverableException | None
        +register(role, process, factory) None
        +check_for_fatal_error() None
        +stop() None
        +run() None
        #_handle_crash(entry) None
    }

    class ApiGatekeeper {
        #_config: ConfigManager
        #_concurrent_sem: Semaphore
        #_fifo: deque[Event]
        #_rpm_times: deque[float]
        #_rph_times: deque[float]
        #_total_cost_usd: float
        +execute(fn, args, kwargs) Any
        #_dispatch_loop() None
        #_can_admit() bool
        #_run_with_retry(fn, args, kwargs) Any
        #_track_cost(response) None
        #_check_budget() None
    }

    class DebateSDK {
        #_config_dir: str
        #_use_processes: bool
        #_sessions: dict[str, DebateOrchestrator]
        +start_debate(topic) str
        +get_transcript(session_id) list[dict]
        +get_verdict(session_id) dict | None
        +get_status() str
        +stop() None
    }

    class ConfigManager {
        +topic: str
        +max_rounds: int
        +father_model: str
        +pro_model: str
        +con_model: str
        +budget_usd: float
        +concurrent_max: int
        +requests_per_minute: int
        +requests_per_hour: int
        +alert_at_usd: float
        +input_cost_per_million: float
        +output_cost_per_million: float
        +llm_timeout: int
        +max_retries: int
    }

    class DebateMessage {
        +message_id: str
        +from_agent: AgentRole
        +to_agent: AgentRole
        +message_type: MessageType
        +round_number: int
        +content: str
        +citations: list[Citation]
        +references_message_id: str | None
        +to_json() str
        +from_json(s)$ DebateMessage
    }

    class Verdict {
        +winner: AgentRole
        +pro_score: float
        +con_score: float
        +justification: str
        +criterion: str
        +rounds_evaluated: int
    }

    class SearchTool {
        +handle_tool_call(inputs) list[Citation]
        +search(query) list[Citation]
    }

    class MessageBus {
        +send_to_pro(msg) None
        +send_to_con(msg) None
        +send_to_father(msg) None
        +receive_from_pro() DebateMessage
        +receive_from_con() DebateMessage
        +receive_from_father() DebateMessage
    }

    BaseAgent <|-- FatherAgent
    BaseAgent <|-- ProAgent
    BaseAgent <|-- ConAgent

    DebateOrchestrator "1" *-- "1" FatherAgent : owns
    DebateOrchestrator "1" *-- "1" ProAgent : owns
    DebateOrchestrator "1" *-- "1" ConAgent : owns
    DebateOrchestrator "1" *-- "0..1" Watchdog : monitors
    DebateOrchestrator "1" --> "1" ConfigManager : reads
    DebateOrchestrator "1" --> "1" ApiGatekeeper : throttles via

    DebateSDK "1" *-- "0..*" DebateOrchestrator : session store

    BaseAgent "1" --> "1" ApiGatekeeper : calls through
    BaseAgent "1" --> "1" ConfigManager : reads
    BaseAgent "1" --> "1" SearchTool : uses

    FatherAgent "1" --> "0..1" MessageBus : routes via (bus mode)
    ProAgent "1" --> "0..1" MessageBus : listens (bus mode)
    ConAgent "1" --> "0..1" MessageBus : listens (bus mode)

    FatherAgent ..> Verdict : produces
    ProAgent ..> DebateMessage : produces
    ConAgent ..> DebateMessage : produces
```

## ASCII Summary (agent message flow)

```
CLI / Terminal
     │
     ▼
 DebateSDK          ← only public interface
     │
     ▼
DebateOrchestrator
     │
     ├──[spawn]──► PRO  Process  ──JSON──►┐
     │                                    │
     ├──[spawn]──► CON  Process  ──JSON──►├──► FATHER Process ──► Verdict
     │                                    │
     └──[spawn]──► FATHER Process◄────────┘

All LLM calls pass through ApiGatekeeper (FIFO + rate-limit + budget).
Watchdog daemon thread monitors all three processes.
```
