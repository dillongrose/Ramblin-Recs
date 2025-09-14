import time, statistics, os, random, requests

API = os.environ.get("API", "http://localhost:8000")

def p95(vals):
    vals = sorted(vals)
    if not vals: return 0
    k = int(round(0.95*(len(vals)-1)))
    return vals[k]

def main():
    lat = []
    for _ in range(30):
        t0 = time.time()
        r = requests.get(f"{API}/events/feed?limit=10", timeout=15)
        r.raise_for_status(); _ = r.json()
        lat.append((time.time()-t0)*1000)
    print(f"Feed latency: avg {statistics.mean(lat):.1f} ms, p95 {p95(lat):.1f} ms")

    # bootstrap a few users and measure personalized feed
    users = []
    pool = ["tech","music","career","sports","arts","social","wellness","volunteering"]
    for i in range(8):
        interests = random.sample(pool, 3)
        r = requests.post(f"{API}/users/bootstrap",
                          json={"email":f"eval{i}@gt.edu","display_name":f"Eval{i}","interests":interests},
                          timeout=15)
        r.raise_for_status()
        users.append(r.json()["id"])

    lat2 = []
    for uid in users:
        t0 = time.time()
        r = requests.get(f"{API}/events/feed?user_id={uid}&limit=10", timeout=15)
        r.raise_for_status(); _ = r.json()
        lat2.append((time.time()-t0)*1000)
    print(f"Personalized feed: avg {statistics.mean(lat2):.1f} ms, p95 {p95(lat2):.1f} ms over {len(lat2)} users")

    print("\nResume line:")
    print(f"- Built an AI event recommender (FastAPI + React + pgvector) with p95 feed latency ~{p95(lat2):.0f} ms; personalized ranking & explanations.")

if __name__ == "__main__":
    main()
