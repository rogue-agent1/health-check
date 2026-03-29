#!/usr/bin/env python3
"""health_check - Service health checker with retry and timeout."""
import sys, time

class HealthCheck:
    def __init__(self, name, check_fn, interval=30, retries=3, timeout=5):
        self.name = name
        self.check_fn = check_fn
        self.interval = interval
        self.retries = retries
        self.timeout = timeout
        self.status = "unknown"
        self.last_check = None
        self.failures = 0
        self.history = []

    def run(self):
        for attempt in range(self.retries):
            try:
                result = self.check_fn()
                self.status = "healthy" if result else "unhealthy"
                self.failures = 0 if result else self.failures + 1
                self.last_check = time.time()
                self.history.append((self.last_check, self.status))
                return self.status
            except Exception as e:
                self.failures += 1
                self.status = "error"
        self.last_check = time.time()
        self.history.append((self.last_check, self.status))
        return self.status

class HealthMonitor:
    def __init__(self):
        self.checks = {}

    def register(self, check):
        self.checks[check.name] = check

    def run_all(self):
        results = {}
        for name, check in self.checks.items():
            results[name] = check.run()
        return results

    def summary(self):
        total = len(self.checks)
        healthy = sum(1 for c in self.checks.values() if c.status == "healthy")
        return {"total": total, "healthy": healthy, "unhealthy": total - healthy}

def test():
    hc = HealthCheck("test", lambda: True)
    assert hc.run() == "healthy"
    assert hc.failures == 0
    hc2 = HealthCheck("bad", lambda: False, retries=1)
    assert hc2.run() == "unhealthy"
    assert hc2.failures == 1
    call_count = [0]
    def flaky():
        call_count[0] += 1
        if call_count[0] <= 2: raise Exception("fail")
        return True
    hc3 = HealthCheck("flaky", flaky, retries=3)
    assert hc3.run() == "healthy"
    mon = HealthMonitor()
    mon.register(HealthCheck("svc1", lambda: True))
    mon.register(HealthCheck("svc2", lambda: False, retries=1))
    results = mon.run_all()
    assert results["svc1"] == "healthy"
    assert results["svc2"] == "unhealthy"
    s = mon.summary()
    assert s["healthy"] == 1 and s["unhealthy"] == 1
    print("All tests passed!")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("health_check: Health checker. Use --test")
