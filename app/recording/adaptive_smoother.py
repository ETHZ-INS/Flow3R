import time
import rx
from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler


def adaptive_smoother(alpha: float = 0.05,
                      init_period: float = 1/30,
                      scheduler=None):
    """
    Return an operator that turns a bursty stream into a steady cadence
    whose period follows an exponential moving average of recent arrivals.
    """
    sched = scheduler or ThreadPoolScheduler(1)     # single FIFO worker

    def _operator(source):
        state = {
            "next_due": None,       # wall-clock time when NEXT item should emit
            "ema": init_period,     # running average period
            "last_arrival": None    # arrival time of the previous input
        }

        def mapper(item):
            now = time.time()

            # update EMA of arrival intervals
            if state["last_arrival"] is not None:
                interval = now - state["last_arrival"]
                state["ema"] = alpha * interval + (1-alpha) * state["ema"]
            state["last_arrival"] = now

            # schedule this item
            if state["next_due"] is None or state["next_due"] < now:
                state["next_due"] = now            # no backlog: emit ASAP

            delay = state["next_due"] - now        # ≥ 0
            state["next_due"] += state["ema"]      # advance for next item

            return rx.of(item).pipe(
                ops.delay(delay, scheduler=sched)
            )

        return source.pipe(ops.flat_map(mapper))

    return _operator
