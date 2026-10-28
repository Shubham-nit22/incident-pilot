# Each case: (incident text, intent, category, acceptable first actions)
# "acceptable_actions" is a list because several fixes can be valid
# An empty list means: this is a question so No fix should be proposed
# The IP addresses are from ranges reserved for documentation and examples.

CASES = [
    # ------- information requests -----
    ("How do i find slow queries in postgreSQL?","info_request","database",[]),
    ("what does pg_stat_statements track and how do i enable it?","info_request","database",[]),
    ("How can i check which indexes PostgreSQL is actually using?","info_request","database",[]),
    ("How do I roll back a Kubernetes Deployment to a previous revision?", "info_request", "deployment", []),
    ("How can I debug a pod that is stuck in the Pending state?", "info_request", "deployment", []),
    ("What is the difference between liveness and readiness probes?", "info_request", "deployment", []),
    ("How does a Kubernetes Service route traffic to pods?", "info_request", "network", []),
    ("How do I debug DNS resolution inside a Kubernetes cluster?", "info_request", "network", []),
    ("What are good ways to defend against credential stuffing?", "info_request", "security", []),
    ("How should session identifiers be managed securely?", "info_request", "security", []),
    ("How can I limit login attempts to prevent brute force attacks?", "info_request", "security", []),


    # --- database incidents -----
    ("The payments database is rejecting new connections with 'too many clients already' and checkout is failing.", "incident", "database", ["restart_service","scale_up"]),
    ("Reporting queries on the main PostgreSQL server went from 2 seconds to over a minuter after the nightly batch job; CPU is at 100 percent.","incident","database",["scale_up","restart_service"]),
    ("The primary PostgreSQL service hung overnight and accepts no queries, although the process is still running.","incident","database",["restart_service"]),
    ("Disk usage on the orders database reached 98 percent and write queries are starting to fail.", "incident", "database", ["scale_up"]),
    ("The product catalog database serves stale prices because its query cache was not invalidated after yesterday's import.", "incident", "database", ["clear_cache"]),
    ("Long-running locks are blocking updates on the inventory table and the application keeps timing out.", "incident", "database", ["restart_service"]),

    # ------ Deployment incidents ----
    ("Our checkout API started returning 500 errors right after today's deploy of version 2.4.1.", "incident", "deployment", ["rollback_deploy"]),
    ("The search service crash-loops since the latest release; the previous release was stable.", "incident", "deployment", ["rollback_deploy"]),
    ("After the 3 pm release, the login page shows a blank screen for every user.", "incident", "deployment", ["rollback_deploy"]),
    ("The billing worker's new release processes some invoices twice.", "incident", "deployment", ["rollback_deploy"]),
    ("The API gateway returns 502 errors since we pushed the new routing configuration ten minutes ago.", "incident", "deployment", ["rollback_deploy"]),
    ("The mobile backend's memory grows until pods are killed; restarting fixes it for an hour, and it began with Monday's deploy.", "incident", "deployment", ["rollback_deploy", "restart_service"]),
    ("Our feature flag service has been up for 40 days and now serves stale flags until it is restarted.", "incident", "deployment", ["restart_service", "clear_cache"]),

    # ----- network incidents -----
    ("Internal DNS lookups fail intermittently and pods cannot resolve the payments service name.", "incident", "network", ["restart_service"]),
    ("The ingress controller stopped routing traffic; all external requests time out while the application pods look healthy.", "incident", "network", ["restart_service"]),
    ("The load balancer marks all backends unhealthy because they cannot accept new connections during a traffic spike.", "incident", "network", ["scale_up"]),
    ("After yesterday's firewall rule update, the partner API can no longer connect to our service.", "incident", "network", ["rollback_deploy"]),
    ("Traffic between the web tier and the cache cluster is dropping packets and connections keep resetting.", "incident", "network", ["restart_service"]),
    ("The service mesh sidecar proxies are returning connection reset errors between our microservices.", "incident", "network", ["restart_service"]),
    ("The VPN gateway for our office stopped accepting connections and engineers cannot reach internal tools.", "incident", "network", ["restart_service"]),

    # ----- security incidents -----
    ("Someone is trying thousands of passwords per minute against our login endpoint from 203.0.113.50.", "incident", "security", ["block_ip"]),
    ("A single IP address, 198.51.100.7, is sending 50,000 requests per minute to our public API and degrading it.", "incident", "security", ["block_ip"]),
    ("We see repeated SQL injection attempts against the search endpoint coming from 192.0.2.44.", "incident", "security", ["block_ip"]),
    ("A scanner from 203.0.113.99 is probing hundreds of admin URLs on our website.", "incident", "security", ["block_ip"]),
    ("Our logs show a credential stuffing attack: thousands of failed logins across many accounts from the 198.51.100.0/24 range.", "incident", "security", ["block_ip"]),
    ("An exposed admin panel is being brute forced by a bot at 192.0.2.150.", "incident", "security", ["block_ip"]),
    ("A denial of service attack from 203.0.113.0/24 is overwhelming our login service.", "incident", "security", ["block_ip", "scale_up"]),


    # ---- other ----
    ("The monitoring dashboard has shown no data for the last hour although all services are running.", "incident","other", ["restart_service"]),
    ("Scheduled email notification have not been sent since this morning.","incident","other",["restart_service"]),

]