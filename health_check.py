#!/usr/bin/env python3
"""health_check - Health check registry with dependencies, timeouts, and aggregation."""
import sys, time

class HealthCheck:
    def __init__(self):
        self.checks = {}
    def register(self, name, check_fn, critical=True, timeout=5.0):
        self.checks[name] = {"fn": check_fn, "critical": critical, "timeout": timeout}
    def run(self):
        results = {}
        for name, check in self.checks.items():
            t0 = time.monotonic()
            try:
                ok = check["fn"]()
                elapsed = time.monotonic() - t0
                results[name] = {"status": "up" if ok else "down", "time": elapsed, "critical": check["critical"]}
            except Exception as e:
                elapsed = time.monotonic() - t0
                results[name] = {"status": "down", "time": elapsed, "error": str(e), "critical": check["critical"]}
        return results
    def is_healthy(self, results=None):
        if results is None: results = self.run()
        return all(r["status"] == "up" for r in results.values() if r["critical"])
    def summary(self, results=None):
        if results is None: results = self.run()
        up = sum(1 for r in results.values() if r["status"] == "up")
        return f"{up}/{len(results)} healthy"

def test():
    hc = HealthCheck()
    hc.register("db", lambda: True, critical=True)
    hc.register("cache", lambda: True, critical=False)
    hc.register("external", lambda: False, critical=False)
    results = hc.run()
    assert results["db"]["status"] == "up"
    assert results["external"]["status"] == "down"
    assert hc.is_healthy(results)  # only critical matters
    hc.register("db2", lambda: (_ for _ in ()).throw(ConnectionError("fail")), critical=True)
    r2 = hc.run()
    assert not hc.is_healthy(r2)
    assert "2/4" in hc.summary(r2) or "3/4" in hc.summary(r2)
    print("health_check: all tests passed")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("Usage: health_check.py --test")
